package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.AuthSession;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.ocr.CsvTradeSignalParser;
import com.trading.investright.ocr.ImageParserService;
import com.trading.investright.ocr.TradeSignalParser;
import com.trading.investright.service.CloudImageFetcher;
import com.trading.investright.service.LocalImageFetcher;
import com.trading.investright.service.OrderService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.awt.image.BufferedImage;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "scheduler.enabled", havingValue = "true")
public class ScheduledTradeExecutor {

    private final SchedulerProperties schedulerProperties;
    private final CloudImageFetcher cloudImageFetcher;
    private final LocalImageFetcher localImageFetcher;
    private final ImageParserService imageParserService;
    private final TradeSignalParser tradeSignalParser;
    private final CsvTradeSignalParser csvTradeSignalParser;
    private final OrderService orderService;
    private final InvestRightAuthClient authClient;

    @Scheduled(cron = "${scheduler.cron:0 55 8 * * *}", zone = "${scheduler.timezone:Asia/Kolkata}")
    public void executeScheduledTrades() {
        LocalDateTime now = LocalDateTime.now(ZoneId.of(schedulerProperties.getTimezone()));
        log.info("=== Scheduled trade execution started at {} ===", now);

        try {
            if (schedulerProperties.isAutoLogin()) {
                performAutoLogin();
            }

            List<TradeSignal> allSignals = loadAndParseImages();

            if (allSignals.isEmpty()) {
                log.info("No trade signals parsed from images. No orders to place.");
                return;
            }

            log.info("Parsed {} trade signals total. Placing orders...", allSignals.size());
            placeOrders(allSignals);

        } catch (Exception ex) {
            log.error("Scheduled trade execution failed: {}", ex.getMessage(), ex);
        }

        log.info("=== Scheduled trade execution completed ===");
    }

    List<TradeSignal> loadAndParseImages() {
        String source = schedulerProperties.getImageSource();
        if ("local".equalsIgnoreCase(source)) {
            return loadFromLocalFolder();
        } else {
            return loadFromCloudUrls();
        }
    }

    private List<TradeSignal> loadFromLocalFolder() {
        String folderPath = schedulerProperties.getLocalFolderPath();
        if (folderPath == null || folderPath.isBlank()) {
            log.warn("No local folder path configured (scheduler.local-folder-path). Skipping.");
            return List.of();
        }

        List<TradeSignal> allSignals = new ArrayList<>();

        log.info("Reading CSV trade signals from folder: {}", folderPath);
        List<TradeSignal> csvSignals = csvTradeSignalParser.parseCsvFilesFromFolder(folderPath);
        if (!csvSignals.isEmpty()) {
            log.info("Parsed {} trade signals from CSV files", csvSignals.size());
            allSignals.addAll(csvSignals);
        }

        log.info("Reading trade signal images from local folder: {}", folderPath);
        List<BufferedImage> images;
        if (schedulerProperties.isUseDateSubfolder()) {
            images = localImageFetcher.fetchTodaysImages(folderPath);
        } else {
            images = localImageFetcher.fetchImagesFromFolder(folderPath);
        }

        for (BufferedImage image : images) {
            try {
                String ocrText = imageParserService.extractText(image);
                log.info("OCR extracted text:\n{}", ocrText);
                List<TradeSignal> signals = tradeSignalParser.parseOcrText(ocrText);
                log.info("Parsed {} signals from image", signals.size());
                allSignals.addAll(signals);
            } catch (Exception ex) {
                log.error("Failed to process image: {}", ex.getMessage());
            }
        }

        if (allSignals.isEmpty()) {
            log.warn("No trade signals found in folder: {}", folderPath);
        }

        return allSignals;
    }

    private List<TradeSignal> loadFromCloudUrls() {
        List<String> imageUrls = getImageUrls();
        if (imageUrls.isEmpty()) {
            log.warn("No image URLs configured. Skipping scheduled execution.");
            return List.of();
        }

        List<TradeSignal> allSignals = new ArrayList<>();
        for (String url : imageUrls) {
            List<TradeSignal> signals = fetchAndParseCloudImage(url);
            allSignals.addAll(signals);
        }
        return allSignals;
    }

    private void performAutoLogin() {
        String username = schedulerProperties.getUsername();
        String password = schedulerProperties.getPassword();
        String twoFaAnswer = schedulerProperties.getTwoFaAnswer();

        if (username == null || username.isBlank()) {
            log.warn("Auto-login credentials not configured. Assuming session is already active.");
            return;
        }

        log.info("Performing auto-login for user: {}", username);
        int attempts = 0;
        while (attempts < schedulerProperties.getRetryAttempts()) {
            try {
                AuthSession session = authClient.performFullLogin(username, password, twoFaAnswer);
                log.info("Auto-login successful. Session expires at: {}", session.getExpiresAt());
                return;
            } catch (Exception ex) {
                attempts++;
                log.error("Auto-login attempt {}/{} failed: {}",
                        attempts, schedulerProperties.getRetryAttempts(), ex.getMessage());
                if (attempts < schedulerProperties.getRetryAttempts()) {
                    try {
                        Thread.sleep(schedulerProperties.getRetryDelayMs());
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Login retry interrupted", ie);
                    }
                }
            }
        }
        throw new RuntimeException("Auto-login failed after " + schedulerProperties.getRetryAttempts() + " attempts");
    }

    private List<String> getImageUrls() {
        List<String> urls = new ArrayList<>();
        if (schedulerProperties.getImageSourceUrl() != null && !schedulerProperties.getImageSourceUrl().isBlank()) {
            urls.add(schedulerProperties.getImageSourceUrl());
        }
        if (schedulerProperties.getImageSourceUrls() != null) {
            urls.addAll(schedulerProperties.getImageSourceUrls());
        }
        return urls;
    }

    List<TradeSignal> fetchAndParseCloudImage(String imageUrl) {
        try {
            BufferedImage image = cloudImageFetcher.fetchImage(imageUrl);
            String ocrText = imageParserService.extractText(image);
            log.info("OCR text from {}:\n{}", imageUrl, ocrText);
            List<TradeSignal> signals = tradeSignalParser.parseOcrText(ocrText);
            log.info("Parsed {} signals from {}", signals.size(), imageUrl);
            return signals;
        } catch (Exception ex) {
            log.error("Failed to process image {}: {}", imageUrl, ex.getMessage());
            return List.of();
        }
    }

    private void placeOrders(List<TradeSignal> signals) {
        String userId = schedulerProperties.getUserId() != null ?
                schedulerProperties.getUserId() : schedulerProperties.getUsername();

        List<OrderRequest> orderRequests = new ArrayList<>();
        for (TradeSignal signal : signals) {
            if (signal.getTransactionType() != null) {
                try {
                    OrderRequest order = orderService.buildOrderFromSignal(signal, null);
                    orderRequests.add(order);
                    log.info("Built order: {} {} {} @ {}",
                            signal.getTransactionType(),
                            signal.getInstrumentName(),
                            order.getQuantity(),
                            signal.getEntryPrice());
                } catch (Exception ex) {
                    log.error("Failed to build order for signal {}: {}",
                            signal.getInstrumentName(), ex.getMessage());
                }
            }
        }

        if (orderRequests.isEmpty()) {
            log.info("No valid orders to place.");
            return;
        }

        log.info("Placing {} orders...", orderRequests.size());
        List<OrderResponse> responses = orderService.placeBulkOrders(orderRequests, userId);

        int success = 0;
        int failed = 0;
        for (OrderResponse response : responses) {
            if ("success".equalsIgnoreCase(response.getStatus())) {
                success++;
                log.info("Order placed successfully: {}", response.getData().getOrderId());
            } else {
                failed++;
                log.error("Order failed: {}", response.getData().getOrderId());
            }
        }
        log.info("Order placement summary: {} succeeded, {} failed out of {} total",
                success, failed, responses.size());
    }
}
