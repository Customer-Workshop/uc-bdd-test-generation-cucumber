package com.trading.investright.controller;

import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.ApiResponse;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.ocr.ImageParserService;
import com.trading.investright.ocr.TradeSignalParser;
import com.trading.investright.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/signals")
@RequiredArgsConstructor
@Tag(name = "Trade Signals", description = "Image-based trade signal parsing and execution")
public class TradeSignalController {

    private final ImageParserService imageParserService;
    private final TradeSignalParser tradeSignalParser;
    private final OrderService orderService;

    @PostMapping(value = "/parse-image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Parse trade signals from image",
            description = "Upload an image containing trade signals. Returns parsed signals for review before placing orders.")
    public ResponseEntity<ApiResponse<List<TradeSignal>>> parseImage(
            @RequestPart("image") MultipartFile image) {
        String ocrText = imageParserService.extractText(image);
        List<TradeSignal> signals = tradeSignalParser.parseOcrText(ocrText);
        return ResponseEntity.ok(ApiResponse.success(
                "Parsed " + signals.size() + " trade signals", signals));
    }

    @PostMapping(value = "/execute-image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Parse and execute trade signals from image",
            description = "Upload an image, parse trade signals, and automatically place all orders")
    public ResponseEntity<ApiResponse<Map<String, Object>>> executeImage(
            @RequestPart("image") MultipartFile image,
            @RequestParam String userId,
            @RequestParam(required = false) Integer quantityOverride) {
        String ocrText = imageParserService.extractText(image);
        List<TradeSignal> signals = tradeSignalParser.parseOcrText(ocrText);

        List<OrderRequest> orderRequests = new ArrayList<>();
        for (TradeSignal signal : signals) {
            if (signal.getTransactionType() != null) {
                OrderRequest order = orderService.buildOrderFromSignal(signal, quantityOverride);
                orderRequests.add(order);
            }
        }

        List<OrderResponse> orderResponses = orderService.placeBulkOrders(orderRequests, userId);

        Map<String, Object> result = new HashMap<>();
        result.put("parsedSignals", signals);
        result.put("ordersPlaced", orderResponses);
        result.put("totalSignals", signals.size());
        result.put("totalOrdersAttempted", orderRequests.size());

        return ResponseEntity.ok(ApiResponse.success("Processed image and placed orders", result));
    }
}
