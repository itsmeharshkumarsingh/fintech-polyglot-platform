package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/websocket"
)

var (
	totalRoutedRequests uint64
	activeConnections   int64
	lastGatewayLatency  int64 // microseconds
)

type WSHub struct {
	clients map[*websocket.Conn]bool
	mu      sync.Mutex
}

var hub = WSHub{
	clients: make(map[*websocket.Conn]bool),
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

func (h *WSHub) Broadcast(event map[string]interface{}) {
	h.mu.Lock()
	defer h.mu.Unlock()
	payload, err := json.Marshal(event)
	if err != nil {
		return
	}
	for conn := range h.clients {
		if err := conn.WriteMessage(websocket.TextMessage, payload); err != nil {
			conn.Close()
			delete(h.clients, conn)
		}
	}
}

type TokenRequest struct {
	MerchantID string `json:"merchant_id"`
	Tier       string `json:"tier"`
}

type GatewayEvaluateRequest struct {
	MerchantID       string  `json:"merchant_id" binding:"required"`
	AmountUSD        float64 `json:"amount_usd" binding:"required"`
	Velocity1H       int     `json:"velocity_1h"`
	CrossBorder      bool    `json:"cross_border"`
	HistoricalCBRate float64 `json:"historical_cb_rate"`
	DisputeClaim     string  `json:"dispute_claim"`
	UseFAISS         bool    `json:"use_faiss"`
	EventType        string  `json:"event_type"`
}

type PayPalOrderResult struct {
	OrderID    string `json:"order_id"`
	Status     string `json:"status"`
	ApproveURL string `json:"approve_url"`
	Mode       string `json:"mode"`
}

func getJWTSecret() []byte {
	sec := os.Getenv("JWT_SECRET")
	if sec == "" {
		sec = "hks_polyglot_super_secret_jwt_signing_key_2026"
	}
	return []byte(sec)
}

func hasRealPayPalKeys() bool {
	cid := strings.TrimSpace(os.Getenv("PAYPAL_CLIENT_ID"))
	sec := strings.TrimSpace(os.Getenv("PAYPAL_CLIENT_SECRET"))
	return cid != "" && sec != "" &&
		cid != "your_paypal_sandbox_client_id_here" &&
		sec != "your_paypal_sandbox_client_secret_here"
}

func getPayPalAccessToken(client *http.Client) (string, error) {
	base := os.Getenv("PAYPAL_API_BASE")
	if base == "" {
		base = "https://api-m.sandbox.paypal.com"
	}
	data := url.Values{}
	data.Set("grant_type", "client_credentials")

	req, err := http.NewRequest("POST", base+"/v1/oauth2/token", strings.NewReader(data.Encode()))
	if err != nil {
		return "", err
	}
	req.SetBasicAuth(strings.TrimSpace(os.Getenv("PAYPAL_CLIENT_ID")), strings.TrimSpace(os.Getenv("PAYPAL_CLIENT_SECRET")))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("paypal oauth status %d", resp.StatusCode)
	}
	var tokenResp struct {
		AccessToken string `json:"access_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&tokenResp); err != nil {
		return "", err
	}
	return tokenResp.AccessToken, nil
}

func createPayPalSandboxOrder(client *http.Client, amountUSD float64, merchantID string, seq uint64) PayPalOrderResult {
	if hasRealPayPalKeys() {
		token, err := getPayPalAccessToken(client)
		if err == nil && token != "" {
			base := os.Getenv("PAYPAL_API_BASE")
			if base == "" {
				base = "https://api-m.sandbox.paypal.com"
			}
			orderPayload := map[string]interface{}{
				"intent": "CAPTURE",
				"purchase_units": []map[string]interface{}{
					{
						"reference_id": merchantID,
						"amount": map[string]string{
							"currency_code": "USD",
							"value":         fmt.Sprintf("%.2f", amountUSD),
						},
					},
				},
			}
			bodyBytes, _ := json.Marshal(orderPayload)
			req, err := http.NewRequest("POST", base+"/v2/checkout/orders", bytes.NewBuffer(bodyBytes))
			if err == nil {
				req.Header.Set("Authorization", "Bearer "+token)
				req.Header.Set("Content-Type", "application/json")
				resp, err := client.Do(req)
				if err == nil {
					defer resp.Body.Close()
					if resp.StatusCode == http.StatusCreated || resp.StatusCode == http.StatusOK {
						var ppOrder struct {
							ID     string `json:"id"`
							Status string `json:"status"`
							Links  []struct {
								Href string `json:"href"`
								Rel  string `json:"rel"`
							} `json:"links"`
						}
						if json.NewDecoder(resp.Body).Decode(&ppOrder) == nil && ppOrder.ID != "" {
							approveURL := "https://www.sandbox.paypal.com/checkoutnow?token=" + ppOrder.ID
							for _, l := range ppOrder.Links {
								if l.Rel == "approve" {
									approveURL = l.Href
									break
								}
							}
							return PayPalOrderResult{
								OrderID:    ppOrder.ID,
								Status:     ppOrder.Status,
								ApproveURL: approveURL,
								Mode:       "PAYPAL_SANDBOX_LIVE_API",
							}
						}
					}
				}
			}
		}
	}

	// Deterministic Sandbox Order Fallback so live demos never break before credentials are set
	simOrderID := fmt.Sprintf("PAYID-SBX-%d%02d", time.Now().Unix()%1000000, seq%100)
	return PayPalOrderResult{
		OrderID:    simOrderID,
		Status:     "CREATED",
		ApproveURL: "https://www.sandbox.paypal.com/checkoutnow?token=" + simOrderID,
		Mode:       "PAYPAL_SANDBOX_EMULATOR",
	}
}

func jwtAuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.Set("auth_mode", "EDGE_DEMO_BYPASS")
			c.Next()
			return
		}
		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Malformed Authorization header"})
			return
		}
		token, err := jwt.Parse(parts[1], func(t *jwt.Token) (interface{}, error) {
			return getJWTSecret(), nil
		})
		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired JWT token"})
			return
		}
		c.Set("auth_mode", "JWT_HS256_VERIFIED")
		c.Next()
	}
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8001"
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	httpClient := &http.Client{
		Timeout: 25 * time.Second,
	}

	// 1. Health & Concurrency Telemetry Endpoint
	r.GET("/health", func(c *gin.Context) {
		ppMode := "PAYPAL_SANDBOX_EMULATOR"
		if hasRealPayPalKeys() {
			ppMode = "PAYPAL_SANDBOX_LIVE_API"
		}
		c.JSON(http.StatusOK, gin.H{
			"status":                   "healthy",
			"service":                  "go-gin-paypal-edge-gateway",
			"paypal_integration_mode":  ppMode,
			"active_goroutines":        runtime.NumGoroutine(),
			"total_routed_requests":    atomic.LoadUint64(&totalRoutedRequests),
			"active_ws_streams":        atomic.LoadInt64(&activeConnections),
			"last_gateway_overhead_us": atomic.LoadInt64(&lastGatewayLatency),
		})
	})

	// 2. Issue Merchant HS256 JWT Session Token
	r.POST("/api/gateway/auth/token", func(c *gin.Context) {
		var req TokenRequest
		if err := c.ShouldBindJSON(&req); err != nil || req.MerchantID == "" {
			req.MerchantID = "PAYPAL-MERCH-8841"
			req.Tier = "ENTERPRISE"
		}
		claims := jwt.MapClaims{
			"merchant_id": req.MerchantID,
			"tier":        req.Tier,
			"iat":         time.Now().Unix(),
			"exp":         time.Now().Add(24 * time.Hour).Unix(),
		}
		token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
		signed, err := token.SignedString(getJWTSecret())
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to sign token"})
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"token":       signed,
			"merchant_id": req.MerchantID,
			"algorithm":   "HS256",
			"expires_in":  "24h",
		})
	})

	// 3. Real-Time WebSocket Telemetry Stream
	r.GET("/ws/telemetry", func(c *gin.Context) {
		conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			return
		}
		hub.mu.Lock()
		hub.clients[conn] = true
		hub.mu.Unlock()
		atomic.AddInt64(&activeConnections, 1)

		defer func() {
			hub.mu.Lock()
			delete(hub.clients, conn)
			hub.mu.Unlock()
			atomic.AddInt64(&activeConnections, -1)
			conn.Close()
		}()

		for {
			if _, _, err := conn.ReadMessage(); err != nil {
				break
			}
		}
	})

	// 4. PayPal Checkout Order Creation + AI Risk Adjudication Endpoint
	r.POST("/api/gateway/evaluate", jwtAuthMiddleware(), func(c *gin.Context) {
		start := time.Now()
		var req GatewayEvaluateRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		reqCount := atomic.AddUint64(&totalRoutedRequests, 1)
		traceID := fmt.Sprintf("PP-GW-%d-%d", time.Now().UnixMilli(), reqCount)
		authMode, _ := c.Get("auth_mode")

		gatewayPreHookUs := time.Since(start).Microseconds()
		atomic.StoreInt64(&lastGatewayLatency, gatewayPreHookUs)

		// Create or Bind PayPal Sandbox Checkout Order v2
		ppOrder := createPayPalSandboxOrder(httpClient, req.AmountUSD, req.MerchantID, reqCount)
		eventType := req.EventType
		if eventType == "" {
			eventType = "CHECKOUT.ORDER.CREATED"
		}

		forwardPayload := map[string]interface{}{
			"merchant_id":        req.MerchantID,
			"amount_usd":         req.AmountUSD,
			"velocity_1h":        req.Velocity1H,
			"cross_border":       req.CrossBorder,
			"historical_cb_rate": req.HistoricalCBRate,
			"dispute_claim":      req.DisputeClaim,
			"use_faiss":          req.UseFAISS,
			"gateway_trace_id":   traceID,
			"paypal_order_id":    ppOrder.OrderID,
			"paypal_approve_url": ppOrder.ApproveURL,
			"paypal_mode":        ppOrder.Mode,
			"paypal_event_type":  eventType,
		}
		bodyBytes, _ := json.Marshal(forwardPayload)

		resp, err := httpClient.Post(
			aiServiceURL+"/api/v1/risk/evaluate",
			"application/json",
			bytes.NewBuffer(bodyBytes),
		)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error":            "Python AI microservice unreachable",
				"gateway_trace_id": traceID,
			})
			return
		}
		defer resp.Body.Close()

		respBytes, _ := io.ReadAll(resp.Body)
		var aiResult map[string]interface{}
		_ = json.Unmarshal(respBytes, &aiResult)

		envelope := gin.H{
			"gateway_telemetry": gin.H{
				"trace_id":            traceID,
				"auth_verification":   authMode,
				"routing_overhead_us": gatewayPreHookUs,
				"active_goroutines":   runtime.NumGoroutine(),
				"routed_sequence_num": reqCount,
			},
			"paypal_sandbox_order": ppOrder,
			"ai_evaluation":        aiResult,
		}

		go hub.Broadcast(envelope)

		c.JSON(resp.StatusCode, envelope)
	})

	// 5. PayPal Webhook Event Receiver (CUSTOMER.DISPUTE.CREATED / PAYMENT.CAPTURE.DENIED)
	r.POST("/api/gateway/paypal/webhook", func(c *gin.Context) {
		var rawWebhook map[string]interface{}
		if err := c.ShouldBindJSON(&rawWebhook); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid PayPal webhook payload"})
			return
		}
		eventType, _ := rawWebhook["event_type"].(string)
		if eventType == "" {
			eventType = "CUSTOMER.DISPUTE.CREATED"
		}
		merchantID, _ := rawWebhook["merchant_id"].(string)
		if merchantID == "" {
			merchantID = "PAYPAL-MERCH-8841"
		}
		amountUSD, ok := rawWebhook["amount_usd"].(float64)
		if !ok || amountUSD <= 0 {
			amountUSD = 1890.0
		}
		reason, _ := rawWebhook["dispute_claim"].(string)
		if reason == "" {
			reason = "PayPal Webhook Event [" + eventType + "]: Buyer opened MERCHANDISE_OR_SERVICE_NOT_RECEIVED / UNAUTHORIZED dispute in PayPal Resolution Center."
		}

		reqCount := atomic.AddUint64(&totalRoutedRequests, 1)
		traceID := fmt.Sprintf("PP-WH-%d-%d", time.Now().UnixMilli(), reqCount)
		ppOrder := createPayPalSandboxOrder(httpClient, amountUSD, merchantID, reqCount)

		forwardPayload := map[string]interface{}{
			"merchant_id":        merchantID,
			"amount_usd":         amountUSD,
			"velocity_1h":        19,
			"cross_border":       true,
			"historical_cb_rate": 1.95,
			"dispute_claim":      reason,
			"use_faiss":          true,
			"gateway_trace_id":   traceID,
			"paypal_order_id":    ppOrder.OrderID,
			"paypal_approve_url": ppOrder.ApproveURL,
			"paypal_mode":        ppOrder.Mode,
			"paypal_event_type":  eventType,
		}
		bodyBytes, _ := json.Marshal(forwardPayload)

		resp, err := httpClient.Post(
			aiServiceURL+"/api/v1/risk/evaluate",
			"application/json",
			bytes.NewBuffer(bodyBytes),
		)
		if err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Python AI microservice unreachable"})
			return
		}
		defer resp.Body.Close()

		var aiResult map[string]interface{}
		_ = json.NewDecoder(resp.Body).Decode(&aiResult)

		c.JSON(http.StatusOK, gin.H{
			"webhook_status":       "PROCESSED_BY_POLYGLOT_GATEWAY",
			"paypal_event_type":    eventType,
			"paypal_sandbox_order": ppOrder,
			"ai_evaluation":        aiResult,
		})
	})

	// 6. Unified Gateway & PayPal Stats Endpoint
	r.GET("/api/gateway/stats", func(c *gin.Context) {
		ppMode := "PAYPAL_SANDBOX_EMULATOR"
		if hasRealPayPalKeys() {
			ppMode = "PAYPAL_SANDBOX_LIVE_API"
		}
		resp, err := httpClient.Get(aiServiceURL + "/api/v1/risk/stats")
		if err != nil {
			c.JSON(http.StatusOK, gin.H{
				"gateway_online":          true,
				"ai_service_online":       false,
				"paypal_integration_mode": ppMode,
				"active_goroutines":       runtime.NumGoroutine(),
			})
			return
		}
		defer resp.Body.Close()
		var stats map[string]interface{}
		_ = json.NewDecoder(resp.Body).Decode(&stats)
		stats["gateway_online"] = true
		stats["paypal_integration_mode"] = ppMode
		stats["active_goroutines"] = runtime.NumGoroutine()
		stats["total_routed_requests"] = atomic.LoadUint64(&totalRoutedRequests)
		stats["last_gateway_overhead_us"] = atomic.LoadInt64(&lastGatewayLatency)
		c.JSON(http.StatusOK, stats)
	})

	r.Run(":" + port)
}