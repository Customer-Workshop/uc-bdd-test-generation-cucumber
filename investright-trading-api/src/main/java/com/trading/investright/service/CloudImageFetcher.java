package com.trading.investright.service;

import com.trading.investright.exception.OcrProcessingException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class CloudImageFetcher {

    private final WebClient.Builder webClientBuilder;

    public BufferedImage fetchImage(String imageUrl) {
        log.info("Fetching trade signal image from: {}", imageUrl);
        try {
            byte[] imageBytes = webClientBuilder.build()
                    .get()
                    .uri(URI.create(imageUrl))
                    .retrieve()
                    .bodyToMono(byte[].class)
                    .block();

            if (imageBytes == null || imageBytes.length == 0) {
                throw new OcrProcessingException("Empty response when fetching image from: " + imageUrl);
            }

            BufferedImage image = ImageIO.read(new ByteArrayInputStream(imageBytes));
            if (image == null) {
                throw new OcrProcessingException("Unable to decode image from URL: " + imageUrl);
            }

            log.info("Successfully fetched image ({}x{}) from: {}", image.getWidth(), image.getHeight(), imageUrl);
            return image;
        } catch (IOException ex) {
            throw new OcrProcessingException("Failed to read fetched image: " + ex.getMessage(), ex);
        } catch (Exception ex) {
            if (ex instanceof OcrProcessingException) {
                throw ex;
            }
            throw new OcrProcessingException("Failed to fetch image from " + imageUrl + ": " + ex.getMessage(), ex);
        }
    }

    public List<BufferedImage> fetchImages(List<String> imageUrls) {
        List<BufferedImage> images = new ArrayList<>();
        for (String url : imageUrls) {
            try {
                images.add(fetchImage(url));
            } catch (Exception ex) {
                log.error("Failed to fetch image from {}: {}", url, ex.getMessage());
            }
        }
        return images;
    }
}
