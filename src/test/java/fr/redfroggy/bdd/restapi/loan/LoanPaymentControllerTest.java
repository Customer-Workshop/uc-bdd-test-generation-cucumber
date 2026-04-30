package fr.redfroggy.bdd.restapi.loan;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@RunWith(SpringRunner.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.DEFINED_PORT, properties = {
        "marvel.api.host=http://localhost:8888"
})
@AutoConfigureMockMvc
public class LoanPaymentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    @Before
    public void setUp() {
        LoanPaymentController.initSampleData();
    }

    @After
    public void tearDown() {
        LoanPaymentController.loans.clear();
        LoanPaymentController.payments.clear();
    }

    @Test
    public void shouldReturnPaymentsForValidLoan() throws Exception {
        MvcResult result = mockMvc.perform(get("/api/loans/L001/payments")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page").value(0))
                .andExpect(jsonPath("$.size").value(20))
                .andExpect(jsonPath("$.totalElements").value(5))
                .andExpect(jsonPath("$.totalPages").value(1))
                .andExpect(jsonPath("$.content.length()").value(5))
                .andReturn();

        String json = result.getResponse().getContentAsString();
        PaymentPageDTO page = objectMapper.readValue(json, PaymentPageDTO.class);
        assertThat(page.getContent()).allMatch(p -> "L001".equals(p.getLoanId()));
    }

    @Test
    public void shouldReturnNotFoundForInvalidLoanId() throws Exception {
        mockMvc.perform(get("/api/loans/INVALID/payments")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.message").value("Loan not found with id: INVALID"));
    }

    @Test
    public void shouldPaginateResults() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("page", "0")
                        .param("size", "2")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page").value(0))
                .andExpect(jsonPath("$.size").value(2))
                .andExpect(jsonPath("$.totalElements").value(5))
                .andExpect(jsonPath("$.totalPages").value(3))
                .andExpect(jsonPath("$.content.length()").value(2));
    }

    @Test
    public void shouldReturnSecondPage() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("page", "1")
                        .param("size", "2")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page").value(1))
                .andExpect(jsonPath("$.content.length()").value(2));
    }

    @Test
    public void shouldReturnLastPageWithRemainingItems() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("page", "2")
                        .param("size", "2")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page").value(2))
                .andExpect(jsonPath("$.content.length()").value(1));
    }

    @Test
    public void shouldReturnEmptyContentForPageBeyondTotal() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("page", "10")
                        .param("size", "20")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(0))
                .andExpect(jsonPath("$.totalElements").value(5));
    }

    @Test
    public void shouldFilterByDateRange() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("startDate", "2024-02-01")
                        .param("endDate", "2024-03-31")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.content.length()").value(3));
    }

    @Test
    public void shouldFilterByStartDateOnly() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("startDate", "2024-03-01")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3));
    }

    @Test
    public void shouldFilterByEndDateOnly() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("endDate", "2024-01-31")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1));
    }

    @Test
    public void shouldFilterByPaymentType() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("paymentType", "MONTHLY")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.content.length()").value(3));
    }

    @Test
    public void shouldFilterByPaymentTypeExtra() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("paymentType", "EXTRA")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].id").value("P003"));
    }

    @Test
    public void shouldFilterByPaymentTypeLateFee() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("paymentType", "LATE_FEE")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].id").value("P005"));
    }

    @Test
    public void shouldCombineDateRangeAndPaymentTypeFilters() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("startDate", "2024-01-01")
                        .param("endDate", "2024-03-31")
                        .param("paymentType", "MONTHLY")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.content.length()").value(3));
    }

    @Test
    public void shouldReturnEmptyWhenNoPaymentsMatchFilter() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("paymentType", "LUMP_SUM")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(0))
                .andExpect(jsonPath("$.content.length()").value(0));
    }

    @Test
    public void shouldReturnPaymentsForSecondLoan() throws Exception {
        mockMvc.perform(get("/api/loans/L002/payments")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(2))
                .andExpect(jsonPath("$.content.length()").value(2));
    }

    @Test
    public void shouldReturnLumpSumPaymentsForSecondLoan() throws Exception {
        mockMvc.perform(get("/api/loans/L002/payments")
                        .param("paymentType", "LUMP_SUM")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].id").value("P007"));
    }

    @Test
    public void shouldReturnBadRequestForNegativePage() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("page", "-1")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").value("Page index must not be less than zero"));
    }

    @Test
    public void shouldReturnBadRequestForZeroSize() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("size", "0")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").value("Page size must not be less than one"));
    }

    @Test
    public void shouldCombinePaginationAndFiltering() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .param("paymentType", "MONTHLY")
                        .param("page", "0")
                        .param("size", "2")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(3))
                .andExpect(jsonPath("$.totalPages").value(2))
                .andExpect(jsonPath("$.content.length()").value(2));
    }

    @Test
    public void shouldReturnDefaultPaginationValues() throws Exception {
        mockMvc.perform(get("/api/loans/L001/payments")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page").value(0))
                .andExpect(jsonPath("$.size").value(20));
    }
}
