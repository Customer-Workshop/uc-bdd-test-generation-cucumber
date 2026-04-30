package com.trading.investright.service;

import com.trading.investright.exception.OcrProcessingException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.List;
import java.util.function.Function;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CloudImageFetcherTest {

    @Mock
    private WebClient.Builder webClientBuilder;

    @Mock
    private WebClient webClient;

    @Mock
    private WebClient.RequestHeadersUriSpec requestHeadersUriSpec;

    @Mock
    private WebClient.RequestHeadersSpec requestHeadersSpec;

    @Mock
    private WebClient.ResponseSpec responseSpec;

    private CloudImageFetcher fetcher;

    @BeforeEach
    void setUp() {
        fetcher = new CloudImageFetcher(webClientBuilder);
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldFetchAndDecodeImage() throws IOException {
        BufferedImage testImage = new BufferedImage(200, 100, BufferedImage.TYPE_INT_RGB);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(testImage, "png", baos);
        byte[] imageBytes = baos.toByteArray();

        when(webClientBuilder.build()).thenReturn(webClient);
        when(webClient.get()).thenReturn(requestHeadersUriSpec);
        when(requestHeadersUriSpec.uri(any(java.net.URI.class))).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(byte[].class)).thenReturn(Mono.just(imageBytes));

        BufferedImage result = fetcher.fetchImage("https://s3.example.com/test.png");

        assertNotNull(result);
        assertEquals(200, result.getWidth());
        assertEquals(100, result.getHeight());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldThrowOnEmptyResponse() {
        when(webClientBuilder.build()).thenReturn(webClient);
        when(webClient.get()).thenReturn(requestHeadersUriSpec);
        when(requestHeadersUriSpec.uri(any(java.net.URI.class))).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(byte[].class)).thenReturn(Mono.just(new byte[0]));

        assertThrows(OcrProcessingException.class, () ->
                fetcher.fetchImage("https://s3.example.com/empty.png"));
    }

    @Test
    void shouldHandleMultipleUrlsWithPartialFailures() {
        CloudImageFetcher spyFetcher = spy(fetcher);
        BufferedImage goodImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_RGB);

        doReturn(goodImage).when(spyFetcher).fetchImage("https://s3.example.com/good.png");
        doThrow(new OcrProcessingException("fail")).when(spyFetcher).fetchImage("https://s3.example.com/bad.png");

        List<BufferedImage> results = spyFetcher.fetchImages(
                List.of("https://s3.example.com/good.png", "https://s3.example.com/bad.png"));

        assertEquals(1, results.size());
    }
}
