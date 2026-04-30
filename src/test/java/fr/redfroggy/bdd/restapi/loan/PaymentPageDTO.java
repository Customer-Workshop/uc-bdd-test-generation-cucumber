package fr.redfroggy.bdd.restapi.loan;

import java.util.List;

public final class PaymentPageDTO {

    private List<PaymentDTO> content;

    private int page;

    private int size;

    private long totalElements;

    private int totalPages;

    public PaymentPageDTO() {
    }

    public PaymentPageDTO(List<PaymentDTO> content, int page, int size, long totalElements, int totalPages) {
        this.content = content;
        this.page = page;
        this.size = size;
        this.totalElements = totalElements;
        this.totalPages = totalPages;
    }

    public List<PaymentDTO> getContent() {
        return content;
    }

    public void setContent(List<PaymentDTO> content) {
        this.content = content;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }

    public int getSize() {
        return size;
    }

    public void setSize(int size) {
        this.size = size;
    }

    public long getTotalElements() {
        return totalElements;
    }

    public void setTotalElements(long totalElements) {
        this.totalElements = totalElements;
    }

    public int getTotalPages() {
        return totalPages;
    }

    public void setTotalPages(int totalPages) {
        this.totalPages = totalPages;
    }
}
