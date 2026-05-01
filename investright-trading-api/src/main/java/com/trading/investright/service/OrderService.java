package com.trading.investright.service;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.client.InvestRightOrderClient;
import com.trading.investright.config.TradingProperties;
import com.trading.investright.exception.OrderValidationException;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.request.ModifyOrderRequest;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class OrderService {

    private final InvestRightOrderClient orderClient;
    private final InvestRightAuthClient authClient;
    private final SymbolMappingService symbolMappingService;
    private final TradingProperties tradingProperties;

    public OrderResponse placeOrder(OrderRequest orderRequest, String userId) {
        validateOrderRequest(orderRequest);
        enrichOrderRequest(orderRequest);
        String accessToken = authClient.getAccessToken(userId);
        return orderClient.placeOrder(orderRequest, accessToken);
    }

    public List<OrderResponse> placeBulkOrders(List<OrderRequest> orderRequests, String userId) {
        String accessToken = authClient.getAccessToken(userId);
        List<OrderResponse> responses = new ArrayList<>();
        for (OrderRequest request : orderRequests) {
            try {
                validateOrderRequest(request);
                enrichOrderRequest(request);
                OrderResponse response = orderClient.placeOrder(request, accessToken);
                responses.add(response);
            } catch (Exception ex) {
                log.error("Failed to place order for {}: {}", request.getSecurityId(), ex.getMessage());
                responses.add(OrderResponse.builder()
                        .status("error")
                        .data(OrderResponse.OrderData.builder()
                                .orderId("FAILED: " + ex.getMessage())
                                .build())
                        .build());
            }
        }
        return responses;
    }

    public OrderResponse modifyOrder(String orderId, ModifyOrderRequest modifyRequest, String userId) {
        String accessToken = authClient.getAccessToken(userId);
        return orderClient.modifyOrder(orderId, modifyRequest, accessToken);
    }

    public OrderResponse cancelOrder(String orderId, String userId) {
        String accessToken = authClient.getAccessToken(userId);
        return orderClient.cancelOrder(orderId, accessToken);
    }

    public Map<String, Object> getOrderStatus(String orderId, String userId) {
        String accessToken = authClient.getAccessToken(userId);
        return orderClient.getSingleOrderStatus(orderId, accessToken);
    }

    public Map<String, Object> getAllOrders(String userId) {
        String accessToken = authClient.getAccessToken(userId);
        return orderClient.getOrderStatus(accessToken);
    }

    public OrderRequest buildOrderFromSignal(TradeSignal signal, Integer quantityOverride) {
        int quantity;
        if (quantityOverride != null) {
            quantity = quantityOverride;
        } else if (signal.getEntryPrice() != null && signal.getEntryPrice() > 0) {
            double capital = signal.getCapitalPerTrade() != null ? signal.getCapitalPerTrade() : tradingProperties.getCapitalPerTrade();
            quantity = (int) (capital / signal.getEntryPrice());
            if (quantity < 1) quantity = 1;
            log.info("Capital allocation: ₹{} / ₹{} = {} lots for {} [source={}]",
                    capital, signal.getEntryPrice(), quantity, signal.getInstrumentName(),
                    signal.getSource() != null ? signal.getSource() : "default");
        } else {
            quantity = tradingProperties.getDefaultLotSize();
        }

        OrderRequest.OrderRequestBuilder builder = OrderRequest.builder()
                .exchange(signal.getExchange() != null ? signal.getExchange() : "NSE")
                .transactionType(signal.getTransactionType())
                .quantity(quantity)
                .validity(tradingProperties.getDefaultValidity())
                .disclosedQuantity(0);

        if (signal.getInstrumentType() == TradeSignal.InstrumentType.EQUITY) {
            builder.instrumentSegment("EQUITY")
                    .securityId(symbolMappingService.mapToSecurityId(signal.getUnderlying()))
                    .product("DELIVERY");
        } else {
            String instrumentSegment = symbolMappingService.determineInstrumentSegment(
                    signal.getUnderlying(), signal.getOptionType(), false);
            builder.instrumentSegment(instrumentSegment)
                    .securityId(signal.getTradingSymbol() != null ?
                            signal.getTradingSymbol() :
                            symbolMappingService.mapToSecurityId(signal.getUnderlying()))
                    .optionType(signal.getOptionType())
                    .strikePrice(signal.getStrikePrice())
                    .underlyingSymbol(symbolMappingService.determineUnderlyingSymbol(signal.getUnderlying()))
                    .product("OVERNIGHT");
        }

        if (signal.getEntryPrice() != null && signal.getEntryPrice() > 0) {
            builder.orderType("SL")
                    .triggerPrice(signal.getEntryPrice())
                    .price(calculateSlippagePrice(signal.getEntryPrice(), signal.getTransactionType()));
        } else {
            builder.orderType("MARKET")
                    .price(0.0)
                    .triggerPrice(0.0);
        }

        return builder.build();
    }

    private double calculateSlippagePrice(double price, String transactionType) {
        double slippage = price * (tradingProperties.getSlippagePercent() / 100.0);
        if ("BUY".equalsIgnoreCase(transactionType)) {
            return Math.round((price + slippage) * 100.0) / 100.0;
        } else {
            return Math.round((price - slippage) * 100.0) / 100.0;
        }
    }

    private void validateOrderRequest(OrderRequest request) {
        if (request.getExchange() == null || request.getExchange().isBlank()) {
            throw new OrderValidationException("Exchange is required");
        }

        String exchange = request.getExchange().toUpperCase();
        if (!List.of("NSE", "BSE", "NFO", "BFO").contains(exchange)) {
            throw new OrderValidationException("Invalid exchange: " + exchange + ". Must be NSE, BSE, NFO, or BFO");
        }
        request.setExchange(exchange);

        if (request.getTransactionType() == null || request.getTransactionType().isBlank()) {
            throw new OrderValidationException("Transaction type is required");
        }

        String txnType = request.getTransactionType().toUpperCase();
        if (!List.of("BUY", "SELL").contains(txnType)) {
            throw new OrderValidationException("Invalid transaction type: " + txnType);
        }
        request.setTransactionType(txnType);

        if (request.getQuantity() == null || request.getQuantity() < 1) {
            throw new OrderValidationException("Quantity must be at least 1");
        }

        String orderType = request.getOrderType();
        if (orderType != null) {
            orderType = orderType.toUpperCase();
            request.setOrderType(orderType);
            if (("SL".equals(orderType) || "SL-M".equals(orderType)) &&
                    (request.getTriggerPrice() == null || request.getTriggerPrice() <= 0)) {
                throw new OrderValidationException("Trigger price is required for stop-loss orders");
            }
            if (("LIMIT".equals(orderType) || "SL".equals(orderType)) &&
                    (request.getPrice() == null || request.getPrice() <= 0)) {
                throw new OrderValidationException("Price is required for LIMIT and SL orders");
            }
        }
    }

    private void enrichOrderRequest(OrderRequest request) {
        if (request.getProduct() == null || request.getProduct().isBlank()) {
            request.setProduct(tradingProperties.getDefaultProduct());
        }
        if (request.getValidity() == null || request.getValidity().isBlank()) {
            request.setValidity(tradingProperties.getDefaultValidity());
        }
        if (request.getTriggerPrice() == null) {
            request.setTriggerPrice(0.0);
        }
        if (request.getDisclosedQuantity() == null) {
            request.setDisclosedQuantity(0);
        }
        if (request.getAmo() == null) {
            request.setAmo(false);
        }
    }
}
