package com.trading.investright.controller;

import com.trading.investright.model.TradeReport;
import com.trading.investright.service.TradeReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/report")
@RequiredArgsConstructor
@Tag(name = "Trade Reports", description = "Trade reports with source-level breakdown")
public class TradeReportController {

    private final TradeReportService reportService;

    @GetMapping
    @Operation(summary = "Get trade report",
            description = "Returns trade report with overall summary and per-source breakdown (telegram, image, csv, s3)")
    public ResponseEntity<TradeReport> getReport(
            @RequestParam(required = false) String source) {
        if (source != null && !source.isBlank()) {
            return ResponseEntity.ok(reportService.generateReportBySource(source));
        }
        return ResponseEntity.ok(reportService.generateReport());
    }
}
