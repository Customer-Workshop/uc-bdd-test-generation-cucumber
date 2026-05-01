package com.trading.investright.ocr;

import com.trading.investright.exception.OcrProcessingException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.services.textract.TextractClient;
import software.amazon.awssdk.services.textract.model.Block;
import software.amazon.awssdk.services.textract.model.BlockType;
import software.amazon.awssdk.services.textract.model.DetectDocumentTextRequest;
import software.amazon.awssdk.services.textract.model.DetectDocumentTextResponse;
import software.amazon.awssdk.services.textract.model.Document;
import software.amazon.awssdk.services.textract.model.TextractException;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

@Slf4j
@Service
@RequiredArgsConstructor
public class ImageParserService {

    private final TextractClient textractClient;

    public String extractText(MultipartFile file) {
        try {
            byte[] imageBytes = file.getBytes();
            return detectText(imageBytes);
        } catch (IOException ex) {
            throw new OcrProcessingException("Failed to read image file: " + ex.getMessage(), ex);
        }
    }

    public String extractText(BufferedImage image) {
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "png", baos);
            byte[] imageBytes = baos.toByteArray();
            return detectText(imageBytes);
        } catch (IOException ex) {
            throw new OcrProcessingException("Failed to convert image to bytes: " + ex.getMessage(), ex);
        }
    }

    public String extractText(byte[] imageBytes) {
        return detectText(imageBytes);
    }

    private String detectText(byte[] imageBytes) {
        try {
            Document document = Document.builder()
                    .bytes(SdkBytes.fromByteArray(imageBytes))
                    .build();

            DetectDocumentTextRequest request = DetectDocumentTextRequest.builder()
                    .document(document)
                    .build();

            DetectDocumentTextResponse response = textractClient.detectDocumentText(request);

            StringBuilder text = new StringBuilder();
            for (Block block : response.blocks()) {
                if (block.blockType() == BlockType.LINE) {
                    text.append(block.text()).append("\n");
                }
            }

            String result = text.toString().trim();
            log.debug("Textract extracted text:\n{}", result);
            return result;
        } catch (TextractException ex) {
            throw new OcrProcessingException("AWS Textract OCR processing failed: " + ex.getMessage(), ex);
        }
    }
}
