package fr.redfroggy.bdd.restapi.user;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public class PartialUserDTO {

    @NotBlank
    @Size(max = 50)
    private String lastName;

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }
}
