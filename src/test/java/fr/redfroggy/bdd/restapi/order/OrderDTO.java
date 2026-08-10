package fr.redfroggy.bdd.restapi.order;

import javax.validation.Valid;
import javax.validation.constraints.Email;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.Size;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class OrderDTO {

    @NotBlank
    private String id;

    @NotBlank
    @Size(max = 50)
    private String customerName;

    @Email
    private String customerEmail;

    private OrderStatus status = OrderStatus.PENDING;

    @Valid
    @NotEmpty
    private List<OrderItemDTO> items = new ArrayList<>();

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    public String getCustomerEmail() {
        return customerEmail;
    }

    public void setCustomerEmail(String customerEmail) {
        this.customerEmail = customerEmail;
    }

    public OrderStatus getStatus() {
        return status;
    }

    public void setStatus(OrderStatus status) {
        this.status = status;
    }

    public List<OrderItemDTO> getItems() {
        return items;
    }

    public void setItems(List<OrderItemDTO> items) {
        this.items = items;
    }

    public BigDecimal getTotal() {
        return items.stream()
                .map(OrderItemDTO::getSubTotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
