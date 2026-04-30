package fr.redfroggy.bdd.restapi.loan;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class LoanPaymentController {

    public static List<LoanDTO> loans = new ArrayList<>();

    public static List<PaymentDTO> payments = new ArrayList<>();

    @GetMapping("/loans/{id}/payments")
    public ResponseEntity<?> getPaymentsByLoanId(
            @PathVariable("id") String loanId,
            @RequestParam(value = "page", defaultValue = "0") int page,
            @RequestParam(value = "size", defaultValue = "20") int size,
            @RequestParam(value = "startDate", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam(value = "endDate", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
            @RequestParam(value = "paymentType", required = false) PaymentType paymentType) {

        if (page < 0) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Page index must not be less than zero"));
        }

        if (size < 1) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Page size must not be less than one"));
        }

        LoanDTO loan = loans.stream()
                .filter(l -> l.getId().equals(loanId))
                .findFirst()
                .orElse(null);

        if (loan == null) {
            return ResponseEntity.status(404)
                    .body(new ErrorResponse(404, "Loan not found with id: " + loanId));
        }

        List<PaymentDTO> loanPayments = payments.stream()
                .filter(p -> p.getLoanId().equals(loanId))
                .collect(Collectors.toList());

        if (startDate != null) {
            loanPayments = loanPayments.stream()
                    .filter(p -> !p.getPaymentDate().isBefore(startDate))
                    .collect(Collectors.toList());
        }

        if (endDate != null) {
            loanPayments = loanPayments.stream()
                    .filter(p -> !p.getPaymentDate().isAfter(endDate))
                    .collect(Collectors.toList());
        }

        if (paymentType != null) {
            loanPayments = loanPayments.stream()
                    .filter(p -> p.getPaymentType() == paymentType)
                    .collect(Collectors.toList());
        }

        long totalElements = loanPayments.size();
        int totalPages = (int) Math.ceil((double) totalElements / size);

        int fromIndex = page * size;
        int toIndex = Math.min(fromIndex + size, loanPayments.size());

        List<PaymentDTO> pageContent;
        if (fromIndex >= loanPayments.size()) {
            pageContent = new ArrayList<>();
        } else {
            pageContent = loanPayments.subList(fromIndex, toIndex);
        }

        PaymentPageDTO pageDTO = new PaymentPageDTO(pageContent, page, size, totalElements, totalPages);

        return ResponseEntity.ok(pageDTO);
    }

    public static void initSampleData() {
        loans.clear();
        payments.clear();

        LoanDTO loan1 = new LoanDTO();
        loan1.setId("L001");
        loan1.setBorrowerName("John Doe");
        loan1.setPrincipalAmount(new BigDecimal("250000.00"));
        loan1.setInterestRate(3.5);
        loan1.setTermMonths(360);
        loans.add(loan1);

        LoanDTO loan2 = new LoanDTO();
        loan2.setId("L002");
        loan2.setBorrowerName("Jane Smith");
        loan2.setPrincipalAmount(new BigDecimal("150000.00"));
        loan2.setInterestRate(4.0);
        loan2.setTermMonths(180);
        loans.add(loan2);

        PaymentDTO p1 = new PaymentDTO();
        p1.setId("P001");
        p1.setLoanId("L001");
        p1.setAmount(new BigDecimal("1122.61"));
        p1.setPaymentDate(LocalDate.of(2024, 1, 15));
        p1.setPaymentType(PaymentType.MONTHLY);
        p1.setDescription("January monthly payment");
        payments.add(p1);

        PaymentDTO p2 = new PaymentDTO();
        p2.setId("P002");
        p2.setLoanId("L001");
        p2.setAmount(new BigDecimal("1122.61"));
        p2.setPaymentDate(LocalDate.of(2024, 2, 15));
        p2.setPaymentType(PaymentType.MONTHLY);
        p2.setDescription("February monthly payment");
        payments.add(p2);

        PaymentDTO p3 = new PaymentDTO();
        p3.setId("P003");
        p3.setLoanId("L001");
        p3.setAmount(new BigDecimal("5000.00"));
        p3.setPaymentDate(LocalDate.of(2024, 3, 1));
        p3.setPaymentType(PaymentType.EXTRA);
        p3.setDescription("Extra payment towards principal");
        payments.add(p3);

        PaymentDTO p4 = new PaymentDTO();
        p4.setId("P004");
        p4.setLoanId("L001");
        p4.setAmount(new BigDecimal("1122.61"));
        p4.setPaymentDate(LocalDate.of(2024, 3, 15));
        p4.setPaymentType(PaymentType.MONTHLY);
        p4.setDescription("March monthly payment");
        payments.add(p4);

        PaymentDTO p5 = new PaymentDTO();
        p5.setId("P005");
        p5.setLoanId("L001");
        p5.setAmount(new BigDecimal("50.00"));
        p5.setPaymentDate(LocalDate.of(2024, 4, 20));
        p5.setPaymentType(PaymentType.LATE_FEE);
        p5.setDescription("Late fee for April");
        payments.add(p5);

        PaymentDTO p6 = new PaymentDTO();
        p6.setId("P006");
        p6.setLoanId("L002");
        p6.setAmount(new BigDecimal("1109.53"));
        p6.setPaymentDate(LocalDate.of(2024, 1, 10));
        p6.setPaymentType(PaymentType.MONTHLY);
        p6.setDescription("January monthly payment");
        payments.add(p6);

        PaymentDTO p7 = new PaymentDTO();
        p7.setId("P007");
        p7.setLoanId("L002");
        p7.setAmount(new BigDecimal("20000.00"));
        p7.setPaymentDate(LocalDate.of(2024, 6, 1));
        p7.setPaymentType(PaymentType.LUMP_SUM);
        p7.setDescription("Lump sum payment");
        payments.add(p7);
    }
}
