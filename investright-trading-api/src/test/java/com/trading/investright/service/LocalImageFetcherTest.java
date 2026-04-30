package com.trading.investright.service;

import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.exception.OcrProcessingException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class LocalImageFetcherTest {

    private LocalImageFetcher fetcher;

    @TempDir
    Path tempDir;

    @BeforeEach
    void setUp() {
        SchedulerProperties schedulerProperties = new SchedulerProperties();
        schedulerProperties.setTimezone("Asia/Kolkata");
        fetcher = new LocalImageFetcher(schedulerProperties);
    }

    @Test
    void shouldReadImagesFromFolder() throws IOException {
        createTestImage(tempDir.resolve("signal1.png"));
        createTestImage(tempDir.resolve("signal2.png"));
        Files.writeString(tempDir.resolve("readme.txt"), "not an image");

        List<BufferedImage> images = fetcher.fetchImagesFromFolder(tempDir.toString());
        assertEquals(2, images.size());
    }

    @Test
    void shouldReturnEmptyForNonexistentFolder() {
        List<BufferedImage> images = fetcher.fetchImagesFromFolder("/nonexistent/path");
        assertTrue(images.isEmpty());
    }

    @Test
    void shouldReturnEmptyForEmptyFolder() {
        List<BufferedImage> images = fetcher.fetchImagesFromFolder(tempDir.toString());
        assertTrue(images.isEmpty());
    }

    @Test
    void shouldFetchSingleImage() throws IOException {
        Path imageFile = tempDir.resolve("test.png");
        createTestImage(imageFile);

        BufferedImage image = fetcher.fetchImage(imageFile.toString());
        assertNotNull(image);
        assertEquals(200, image.getWidth());
        assertEquals(100, image.getHeight());
    }

    @Test
    void shouldThrowForMissingFile() {
        assertThrows(OcrProcessingException.class, () ->
                fetcher.fetchImage("/nonexistent/image.png"));
    }

    @Test
    void shouldUseDateSubfolderWhenPresent() throws IOException {
        String today = LocalDate.now(ZoneId.of("Asia/Kolkata")).format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        Path dateFolder = tempDir.resolve(today);
        Files.createDirectories(dateFolder);
        createTestImage(dateFolder.resolve("today-signal.png"));
        createTestImage(tempDir.resolve("old-signal.png"));

        List<BufferedImage> images = fetcher.fetchTodaysImages(tempDir.toString());
        assertEquals(1, images.size());
    }

    @Test
    void shouldFallbackToMainFolderIfNoDateSubfolder() throws IOException {
        createTestImage(tempDir.resolve("signal.png"));

        List<BufferedImage> images = fetcher.fetchTodaysImages(tempDir.toString());
        assertEquals(1, images.size());
    }

    @Test
    void shouldSupportMultipleImageFormats() throws IOException {
        createTestImage(tempDir.resolve("image.png"));
        createTestImage(tempDir.resolve("image.jpg"), "jpg");
        createTestImage(tempDir.resolve("image.bmp"), "bmp");

        List<BufferedImage> images = fetcher.fetchImagesFromFolder(tempDir.toString());
        assertEquals(3, images.size());
    }

    private void createTestImage(Path path) throws IOException {
        createTestImage(path, "png");
    }

    private void createTestImage(Path path, String format) throws IOException {
        BufferedImage image = new BufferedImage(200, 100, BufferedImage.TYPE_INT_RGB);
        ImageIO.write(image, format, path.toFile());
    }
}
