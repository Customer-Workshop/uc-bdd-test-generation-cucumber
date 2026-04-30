package com.trading.investright.service;

import com.trading.investright.exception.OcrProcessingException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class LocalImageFetcher {

    private static final List<String> SUPPORTED_EXTENSIONS = List.of(".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp");

    public List<BufferedImage> fetchImagesFromFolder(String folderPath) {
        Path folder = Paths.get(folderPath);
        if (!Files.exists(folder)) {
            log.warn("Local folder does not exist: {}", folderPath);
            return List.of();
        }
        if (!Files.isDirectory(folder)) {
            log.warn("Path is not a directory: {}", folderPath);
            return List.of();
        }

        List<BufferedImage> images = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(folder)) {
            for (Path file : stream) {
                if (isImageFile(file)) {
                    try {
                        BufferedImage image = ImageIO.read(file.toFile());
                        if (image != null) {
                            images.add(image);
                            log.info("Loaded image: {} ({}x{})", file.getFileName(), image.getWidth(), image.getHeight());
                        } else {
                            log.warn("Unable to decode image: {}", file.getFileName());
                        }
                    } catch (IOException ex) {
                        log.error("Failed to read image {}: {}", file.getFileName(), ex.getMessage());
                    }
                }
            }
        } catch (IOException ex) {
            throw new OcrProcessingException("Failed to read folder " + folderPath + ": " + ex.getMessage(), ex);
        }

        log.info("Loaded {} images from {}", images.size(), folderPath);
        return images;
    }

    public List<BufferedImage> fetchTodaysImages(String folderPath) {
        String today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        Path todayFolder = Paths.get(folderPath, today);

        if (Files.exists(todayFolder) && Files.isDirectory(todayFolder)) {
            log.info("Found today's subfolder: {}", todayFolder);
            return fetchImagesFromFolder(todayFolder.toString());
        }

        log.info("No date subfolder found, reading all images from: {}", folderPath);
        return fetchImagesFromFolder(folderPath);
    }

    public BufferedImage fetchImage(String filePath) {
        Path file = Paths.get(filePath);
        if (!Files.exists(file)) {
            throw new OcrProcessingException("Image file not found: " + filePath);
        }
        try {
            BufferedImage image = ImageIO.read(file.toFile());
            if (image == null) {
                throw new OcrProcessingException("Unable to decode image: " + filePath);
            }
            log.info("Loaded image: {} ({}x{})", file.getFileName(), image.getWidth(), image.getHeight());
            return image;
        } catch (IOException ex) {
            throw new OcrProcessingException("Failed to read image " + filePath + ": " + ex.getMessage(), ex);
        }
    }

    private boolean isImageFile(Path file) {
        if (!Files.isRegularFile(file)) return false;
        String name = file.getFileName().toString().toLowerCase();
        return SUPPORTED_EXTENSIONS.stream().anyMatch(name::endsWith);
    }
}
