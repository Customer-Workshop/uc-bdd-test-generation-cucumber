package com.trading.investright.service;

import com.trading.investright.config.AwsProperties;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.ocr.CsvTradeSignalParser;
import com.trading.investright.ocr.ImageParserService;
import com.trading.investright.ocr.TradeSignalParser;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import software.amazon.awssdk.core.ResponseInputStream;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Request;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Response;
import software.amazon.awssdk.services.s3.model.S3Object;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class S3TradeSignalFetcherTest {

    @Mock
    private S3Client s3Client;

    @Mock
    private AwsProperties awsProperties;

    @Mock
    private SchedulerProperties schedulerProperties;

    @Mock
    private ImageParserService imageParserService;

    @Mock
    private TradeSignalParser tradeSignalParser;

    @Mock
    private CsvTradeSignalParser csvTradeSignalParser;

    private S3TradeSignalFetcher fetcher;

    @BeforeEach
    void setUp() {
        fetcher = new S3TradeSignalFetcher(s3Client, awsProperties, schedulerProperties,
                imageParserService, tradeSignalParser, csvTradeSignalParser);
    }

    @Test
    void shouldBuildPrefixWithDateSubfolder() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setPrefix("trade-signals/");
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(true);
        when(schedulerProperties.getTimezone()).thenReturn("Asia/Kolkata");

        String prefix = fetcher.buildTodayPrefix();

        String today = LocalDate.now(ZoneId.of("Asia/Kolkata")).format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        assertEquals("trade-signals/" + today + "/", prefix);
    }

    @Test
    void shouldBuildPrefixWithoutDateSubfolder() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setPrefix("signals/");
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        String prefix = fetcher.buildTodayPrefix();

        assertEquals("signals/", prefix);
    }

    @Test
    void shouldReturnEmptyWhenNoFilesInS3() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setBucketName("my-bucket");
        s3Props.setPrefix("signals/");
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        ListObjectsV2Response emptyResponse = ListObjectsV2Response.builder()
                .contents(List.of())
                .isTruncated(false)
                .build();
        when(s3Client.listObjectsV2(any(ListObjectsV2Request.class))).thenReturn(emptyResponse);

        List<TradeSignal> signals = fetcher.fetchAndParseSignals();

        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldParseCsvFromS3() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setBucketName("my-bucket");
        s3Props.setPrefix("signals/");
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        S3Object csvObj = S3Object.builder().key("signals/trades.csv").size(100L).build();
        ListObjectsV2Response listResponse = ListObjectsV2Response.builder()
                .contents(List.of(csvObj))
                .isTruncated(false)
                .build();
        when(s3Client.listObjectsV2(any(ListObjectsV2Request.class))).thenReturn(listResponse);

        String csvContent = "symbol,entry,sl,target1,type\nRELIANCE,2500,2450,2600,BUY\n";
        ResponseInputStream<GetObjectResponse> csvStream = new ResponseInputStream<>(
                GetObjectResponse.builder().build(),
                new ByteArrayInputStream(csvContent.getBytes(StandardCharsets.UTF_8)));
        when(s3Client.getObject(any(GetObjectRequest.class))).thenReturn(csvStream);

        String[] headers = {"symbol", "entry", "sl", "target1", "type"};
        when(csvTradeSignalParser.parseHeaders("symbol,entry,sl,target1,type")).thenReturn(headers);

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .entryPrice(2500.0)
                .stopLoss(2450.0)
                .target1(2600.0)
                .transactionType("BUY")
                .build();
        when(csvTradeSignalParser.parseCsvRow(eq(headers), anyString())).thenReturn(signal);

        List<TradeSignal> signals = fetcher.fetchAndParseSignals();

        assertEquals(1, signals.size());
        assertEquals("RELIANCE", signals.get(0).getInstrumentName());
        assertEquals(2500.0, signals.get(0).getEntryPrice());
    }

    @Test
    void shouldContinueOnS3Error() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setBucketName("my-bucket");
        s3Props.setPrefix("signals/");
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        S3Object badObj = S3Object.builder().key("signals/bad.csv").size(100L).build();
        ListObjectsV2Response listResponse = ListObjectsV2Response.builder()
                .contents(List.of(badObj))
                .isTruncated(false)
                .build();
        when(s3Client.listObjectsV2(any(ListObjectsV2Request.class))).thenReturn(listResponse);
        when(s3Client.getObject(any(GetObjectRequest.class))).thenThrow(new RuntimeException("Access denied"));

        List<TradeSignal> signals = fetcher.fetchAndParseSignals();

        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldHandleNullPrefix() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setPrefix(null);
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        String prefix = fetcher.buildTodayPrefix();

        assertEquals("", prefix);
    }

    @Test
    void shouldSkipUnsupportedFileTypes() {
        AwsProperties.S3Properties s3Props = new AwsProperties.S3Properties();
        s3Props.setBucketName("my-bucket");
        s3Props.setPrefix("signals/");
        when(awsProperties.getS3()).thenReturn(s3Props);
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        S3Object txtObj = S3Object.builder().key("signals/readme.txt").size(100L).build();
        ListObjectsV2Response listResponse = ListObjectsV2Response.builder()
                .contents(List.of(txtObj))
                .isTruncated(false)
                .build();
        when(s3Client.listObjectsV2(any(ListObjectsV2Request.class))).thenReturn(listResponse);

        List<TradeSignal> signals = fetcher.fetchAndParseSignals();

        assertTrue(signals.isEmpty());
        verify(s3Client, never()).getObject(any(GetObjectRequest.class));
    }

    @Test
    void shouldHandlePaginatedResults() {
        S3Object obj1 = S3Object.builder().key("signals/readme.txt").size(50L).build();
        ListObjectsV2Response page1 = ListObjectsV2Response.builder()
                .contents(List.of(obj1))
                .isTruncated(true)
                .nextContinuationToken("token123")
                .build();

        S3Object obj2 = S3Object.builder().key("signals/notes.md").size(30L).build();
        ListObjectsV2Response page2 = ListObjectsV2Response.builder()
                .contents(List.of(obj2))
                .isTruncated(false)
                .build();

        when(s3Client.listObjectsV2(any(ListObjectsV2Request.class)))
                .thenReturn(page1)
                .thenReturn(page2);

        List<S3Object> objects = fetcher.listObjects("my-bucket", "signals/");

        assertEquals(2, objects.size());
        verify(s3Client, times(2)).listObjectsV2(any(ListObjectsV2Request.class));
    }
}
