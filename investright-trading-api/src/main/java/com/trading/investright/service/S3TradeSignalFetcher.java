package com.trading.investright.service;

import com.trading.investright.config.AwsProperties;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.exception.OcrProcessingException;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.ocr.CsvTradeSignalParser;
import com.trading.investright.ocr.ImageParserService;
import com.trading.investright.ocr.TradeSignalParser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.core.ResponseInputStream;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Request;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Response;
import software.amazon.awssdk.services.s3.model.S3Object;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnProperty(name = "scheduler.image-source", havingValue = "s3")
public class S3TradeSignalFetcher {

    private final S3Client s3Client;
    private final AwsProperties awsProperties;
    private final SchedulerProperties schedulerProperties;
    private final ImageParserService imageParserService;
    private final TradeSignalParser tradeSignalParser;
    private final CsvTradeSignalParser csvTradeSignalParser;

    private static final Set<String> IMAGE_EXTENSIONS = Set.of(".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp");
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    public List<TradeSignal> fetchAndParseSignals() {
        String bucket = awsProperties.getS3().getBucketName();
        String prefix = buildTodayPrefix();

        log.info("Fetching trade signals from S3: s3://{}/{}", bucket, prefix);

        List<S3Object> objects = listObjects(bucket, prefix);
        if (objects.isEmpty()) {
            log.info("No trade signal files found in S3 at s3://{}/{}", bucket, prefix);
            return List.of();
        }

        List<TradeSignal> allSignals = new ArrayList<>();

        for (S3Object obj : objects) {
            String key = obj.key();
            try {
                if (isCsvFile(key)) {
                    List<TradeSignal> csvSignals = parseCsvFromS3(bucket, key);
                    allSignals.addAll(csvSignals);
                } else if (isImageFile(key)) {
                    List<TradeSignal> imageSignals = parseImageFromS3(bucket, key);
                    allSignals.addAll(imageSignals);
                } else {
                    log.debug("Skipping unsupported file type: {}", key);
                }
            } catch (Exception ex) {
                log.error("Failed to process S3 object {}: {}", key, ex.getMessage());
            }
        }

        log.info("Parsed {} trade signals from S3", allSignals.size());
        return allSignals;
    }

    String buildTodayPrefix() {
        String basePrefix = awsProperties.getS3().getPrefix();
        if (basePrefix == null) basePrefix = "";
        if (!basePrefix.isEmpty() && !basePrefix.endsWith("/")) {
            basePrefix += "/";
        }

        if (schedulerProperties.isUseDateSubfolder()) {
            String timezone = schedulerProperties.getTimezone() != null ? schedulerProperties.getTimezone() : "Asia/Kolkata";
            String today = LocalDate.now(ZoneId.of(timezone)).format(DATE_FMT);
            return basePrefix + today + "/";
        }
        return basePrefix;
    }

    List<S3Object> listObjects(String bucket, String prefix) {
        List<S3Object> allObjects = new ArrayList<>();
        String continuationToken = null;

        do {
            ListObjectsV2Request.Builder requestBuilder = ListObjectsV2Request.builder()
                    .bucket(bucket)
                    .prefix(prefix);

            if (continuationToken != null) {
                requestBuilder.continuationToken(continuationToken);
            }

            ListObjectsV2Response response = s3Client.listObjectsV2(requestBuilder.build());
            allObjects.addAll(response.contents());
            continuationToken = response.isTruncated() ? response.nextContinuationToken() : null;
        } while (continuationToken != null);

        log.info("Found {} files in s3://{}/{}", allObjects.size(), bucket, prefix);
        return allObjects;
    }

    List<TradeSignal> parseCsvFromS3(String bucket, String key) {
        log.info("Parsing CSV from S3: {}", key);
        try (ResponseInputStream<GetObjectResponse> stream = s3Client.getObject(
                GetObjectRequest.builder().bucket(bucket).key(key).build())) {

            BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
            String headerLine = reader.readLine();
            if (headerLine == null) {
                log.warn("Empty CSV file in S3: {}", key);
                return List.of();
            }

            String[] headers = csvTradeSignalParser.parseHeaders(headerLine);
            List<TradeSignal> signals = new ArrayList<>();
            String line;
            int lineNum = 1;
            while ((line = reader.readLine()) != null) {
                lineNum++;
                line = line.trim();
                if (line.isEmpty()) continue;
                try {
                    TradeSignal signal = csvTradeSignalParser.parseCsvRow(headers, line);
                    if (signal != null) {
                        signals.add(signal);
                    }
                } catch (Exception ex) {
                    log.warn("Failed to parse CSV line {} from {}: {}", lineNum, key, ex.getMessage());
                }
            }

            log.info("Parsed {} signals from S3 CSV: {}", signals.size(), key);
            return signals;
        } catch (IOException ex) {
            log.error("Failed to read CSV from S3 {}: {}", key, ex.getMessage());
            return List.of();
        }
    }

    List<TradeSignal> parseImageFromS3(String bucket, String key) {
        log.info("Parsing image from S3: {}", key);
        try (ResponseInputStream<GetObjectResponse> stream = s3Client.getObject(
                GetObjectRequest.builder().bucket(bucket).key(key).build())) {

            BufferedImage image = ImageIO.read(stream);
            if (image == null) {
                throw new OcrProcessingException("Unable to decode image from S3: " + key);
            }

            String ocrText = imageParserService.extractText(image);
            log.info("OCR text from S3 image {}:\n{}", key, ocrText);
            List<TradeSignal> signals = tradeSignalParser.parseOcrText(ocrText);
            log.info("Parsed {} signals from S3 image: {}", signals.size(), key);
            return signals;
        } catch (IOException ex) {
            log.error("Failed to read image from S3 {}: {}", key, ex.getMessage());
            return List.of();
        }
    }

    private boolean isCsvFile(String key) {
        return key.toLowerCase().endsWith(".csv");
    }

    private boolean isImageFile(String key) {
        String lower = key.toLowerCase();
        return IMAGE_EXTENSIONS.stream().anyMatch(lower::endsWith);
    }
}
