package fr.redfroggy.bdd.restapi.user;

import javax.validation.constraints.Email;
import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;
import java.util.List;

public final class UserDTO extends PartialUserDTO {

    @NotBlank
    private String id;

    @NotBlank
    @Size(max = 50)
    private String firstName;

    @Email
    private String email;

    @Min(0)
    @Max(150)
    private int age;

    private UserDTO relatedTo;

    private List<String> sessionIds;

    private UserDetailsDTO details;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public UserDTO getRelatedTo() {
        return relatedTo;
    }

    public void setRelatedTo(UserDTO relatedTo) {
        this.relatedTo = relatedTo;
    }

    public List<String> getSessionIds() {
        return sessionIds;
    }

    public void setSessionIds(List<String> sessionIds) {
        this.sessionIds = sessionIds;
    }

    public UserDetailsDTO getDetails() {
        return details;
    }

    public void setDetails(UserDetailsDTO details) {
        this.details = details;
    }
}
