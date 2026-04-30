package com.trading.investright.controller;

import com.trading.investright.model.TradeSignal;
import com.trading.investright.ocr.ImageParserService;
import com.trading.investright.ocr.TradeSignalParser;
import com.trading.investright.service.OrderService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TradeSignalController.class)
class TradeSignalControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ImageParserService imageParserService;

    @MockBean
    private TradeSignalParser tradeSignalParser;

    @MockBean
    private OrderService orderService;

    @Test
    @WithMockUser
    void shouldParseImage() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "image", "test.png", "image/png", "test image content".getBytes());

        when(imageParserService.extractText(any(org.springframework.web.multipart.MultipartFile.class)))
                .thenReturn("MAZDOCK 2760CE BUY ABOVE 150 SL 120");

        List<TradeSignal> signals = List.of(
                TradeSignal.builder()
                        .instrumentName("MAZDOCK 2760CE")
                        .underlying("MAZDOCK")
                        .strikePrice(2760.0)
                        .optionType("CE")
                        .instrumentType(TradeSignal.InstrumentType.CALL_OPTION)
                        .transactionType("BUY")
                        .entryPrice(150.0)
                        .stopLoss(120.0)
                        .build()
        );
        when(tradeSignalParser.parseOcrText(anyString())).thenReturn(signals);

        mockMvc.perform(multipart("/api/signals/parse-image")
                        .file(file)
                        .with(csrf()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.data[0].underlying").value("MAZDOCK"))
                .andExpect(jsonPath("$.data[0].optionType").value("CE"));
    }
}
