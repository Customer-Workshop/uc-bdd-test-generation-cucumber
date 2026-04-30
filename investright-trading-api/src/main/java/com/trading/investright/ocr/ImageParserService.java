package com.trading.investright.ocr;

import com.trading.investright.exception.OcrProcessingException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.InputStream;

@Slf4j
@Service
@RequiredArgsConstructor
public class ImageParserService {

    private final Tesseract tesseract;

    public String extractText(MultipartFile file) {
        try (InputStream inputStream = file.getInputStream()) {
            BufferedImage image = ImageIO.read(inputStream);
            if (image == null) {
                throw new OcrProcessingException("Unable to read image file. Supported formats: PNG, JPG, TIFF, BMP");
            }
            BufferedImage processed = preprocessImage(image);
            String text = tesseract.doOCR(processed);
            log.debug("OCR extracted text:\n{}", text);
            return text;
        } catch (IOException ex) {
            throw new OcrProcessingException("Failed to read image file: " + ex.getMessage(), ex);
        } catch (TesseractException ex) {
            throw new OcrProcessingException("OCR processing failed: " + ex.getMessage(), ex);
        }
    }

    public String extractText(BufferedImage image) {
        try {
            BufferedImage processed = preprocessImage(image);
            return tesseract.doOCR(processed);
        } catch (TesseractException ex) {
            throw new OcrProcessingException("OCR processing failed: " + ex.getMessage(), ex);
        }
    }

    private BufferedImage preprocessImage(BufferedImage original) {
        BufferedImage grayscale = new BufferedImage(
                original.getWidth(), original.getHeight(), BufferedImage.TYPE_BYTE_GRAY);
        Graphics2D g2d = grayscale.createGraphics();
        g2d.drawImage(original, 0, 0, null);
        g2d.dispose();

        BufferedImage scaled = grayscale;
        if (original.getWidth() < 1000) {
            int newWidth = original.getWidth() * 2;
            int newHeight = original.getHeight() * 2;
            scaled = new BufferedImage(newWidth, newHeight, BufferedImage.TYPE_BYTE_GRAY);
            Graphics2D g = scaled.createGraphics();
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            g.drawImage(grayscale, 0, 0, newWidth, newHeight, null);
            g.dispose();
        }

        return applyThreshold(scaled, 128);
    }

    private BufferedImage applyThreshold(BufferedImage image, int threshold) {
        BufferedImage result = new BufferedImage(image.getWidth(), image.getHeight(), BufferedImage.TYPE_BYTE_BINARY);
        for (int y = 0; y < image.getHeight(); y++) {
            for (int x = 0; x < image.getWidth(); x++) {
                int rgb = image.getRGB(x, y);
                int gray = rgb & 0xFF;
                result.setRGB(x, y, gray > threshold ? 0xFFFFFF : 0x000000);
            }
        }
        return result;
    }
}
