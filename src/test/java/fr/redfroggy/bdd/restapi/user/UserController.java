package fr.redfroggy.bdd.restapi.user;

import com.opencsv.bean.CsvToBean;
import com.opencsv.bean.CsvToBeanBuilder;
import org.junit.Assert;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import wiremock.org.apache.commons.lang3.StringUtils;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.*;
import java.util.stream.Collectors;
import java.util.regex.Pattern;

@RestController
@RequestMapping("/api")
public final class UserController {

    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");
    private static final int MAX_NAME_LENGTH = 100;

    private final UserDetailService userDetailService;

    public UserController(UserDetailService userDetailService) {
        this.userDetailService = userDetailService;
    }

    public static List<UserDTO> users = new ArrayList<>();

    @GetMapping("/users")
    public ResponseEntity<?> getAll(
            @RequestParam(value = "name", required = false) String name,
            @RequestParam(value = "page", required = false) Integer page,
            @RequestParam(value = "size", required = false) Integer size,
            @RequestParam(value = "sort", required = false) String sort) {

        List<UserDTO> result = users;

        if (StringUtils.isNotBlank(name)) {
            result = result.stream().filter(u -> u.getFirstName().toLowerCase().contains(name.toLowerCase())
                    || u.getLastName().toLowerCase().contains(name.toLowerCase()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(sort)) {
            String[] parts = sort.split(",");
            String field = parts[0];
            boolean ascending = parts.length < 2 || "asc".equalsIgnoreCase(parts[1]);

            Comparator<UserDTO> comparator;
            switch (field) {
                case "firstName":
                    comparator = Comparator.comparing(UserDTO::getFirstName, String.CASE_INSENSITIVE_ORDER);
                    break;
                case "lastName":
                    comparator = Comparator.comparing(UserDTO::getLastName, String.CASE_INSENSITIVE_ORDER);
                    break;
                case "age":
                    comparator = Comparator.comparingInt(UserDTO::getAge);
                    break;
                default:
                    comparator = Comparator.comparing(UserDTO::getId);
            }
            if (!ascending) {
                comparator = comparator.reversed();
            }
            result = result.stream().sorted(comparator).collect(Collectors.toList());
        }

        if (page != null && size != null) {
            int fromIndex = page * size;
            if (fromIndex >= result.size()) {
                return ResponseEntity.ok(Collections.emptyList());
            }
            int toIndex = Math.min(fromIndex + size, result.size());
            result = result.subList(fromIndex, toIndex);
        }

        return ResponseEntity.ok(result);
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<UserDTO> get(@PathVariable("id") String id, @RequestParam(required = false) String format) {
        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(id)).findFirst()
                .orElse(null);
        if (currentUser == null) {
            return ResponseEntity
                    .notFound().build();
        }

        ResponseEntity<UserDetailsDTO> responseUserDetails = userDetailService.getUserDetails(currentUser.getId(), format);
        Assert.assertNotNull(responseUserDetails);
        if (!responseUserDetails.getStatusCode().is2xxSuccessful()) {
            return ResponseEntity.badRequest()
                    .build();
        }
        currentUser.setDetails(responseUserDetails.getBody());

        return ResponseEntity.
                ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(currentUser);
    }

    @PostMapping(value = "/users")
    public ResponseEntity<?> addUser(@RequestBody  UserDTO user) {

        // Validate required fields
        if (StringUtils.isBlank(user.getId())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "id is required"));
        }
        if (StringUtils.isBlank(user.getFirstName())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "firstName is required"));
        }
        if (StringUtils.isBlank(user.getLastName())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "lastName is required"));
        }

        // Validate name length
        if (user.getFirstName().length() > MAX_NAME_LENGTH) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "firstName exceeds maximum length of " + MAX_NAME_LENGTH));
        }
        if (user.getLastName().length() > MAX_NAME_LENGTH) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "lastName exceeds maximum length of " + MAX_NAME_LENGTH));
        }

        // Validate email format if provided
        if (StringUtils.isNotBlank(user.getEmail()) && !EMAIL_PATTERN.matcher(user.getEmail()).matches()) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "invalid email format"));
        }

        // Check for duplicate ID
        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(user.getId())).findFirst()
                .orElse(null);
        if (currentUser != null) {
            return ResponseEntity.status(409)
                    .body(Collections.singletonMap("error", "user with id " + user.getId() + " already exists"));
        }

        users.add(user);
        return ResponseEntity.status(201)
                .body(user);
    }

    @PostMapping(value = "/users", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<List<UserDTO>> uploadFile(@RequestParam(name = "file") MultipartFile file) throws IOException {

        CsvToBean<UserCsvLine> csvBean = new CsvToBeanBuilder<UserCsvLine>(new InputStreamReader(file.getInputStream()))
                .withType(UserCsvLine.class)  // Convert a csv string line to PaymentIdentityAuditImportCsvLine
                .withIgnoreLeadingWhiteSpace(true) // White space in front of a quote in a field is ignored
                .withSeparator(';')
                .build();

        Assert.assertNotNull(csvBean);
        List<UserDTO> csvUsers = csvBean.parse()
                .stream()
                .map(userCsvLine -> {
                    UserDTO userDTO = new UserDTO();
                    userDTO.setId(userCsvLine.getId());
                    userDTO.setAge(userCsvLine.getAge());
                    userDTO.setFirstName(userCsvLine.getFirstName());
                    userDTO.setLastName(userCsvLine.getLastName());

                    return userDTO;
                })
                .collect(Collectors.toList());

        users.addAll(csvUsers);

        return ResponseEntity.ok(csvUsers);
    }

    @PutMapping(value = "/users/{id}")
    public ResponseEntity<UserDTO> updateUser(@RequestBody  UserDTO user, @PathVariable String id) {

        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(id)).findFirst()
                .orElse(null);
        if (currentUser == null) {
            return ResponseEntity
                    .notFound().build();
        }

        users.stream().filter(u -> id.equals(u.getId())).forEach(u -> {
            u.setFirstName(user.getFirstName());
            u.setLastName(user.getLastName());
            u.setAge(user.getAge());
            u.setRelatedTo(user.getRelatedTo());
        });

        return ResponseEntity.
                ok(user);
    }

    @PatchMapping(value = "/users/{id}")
    public ResponseEntity<UserDTO> patchUser(@RequestBody  PartialUserDTO user, @PathVariable String id) {

        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(id)).findFirst()
                .orElse(null);
        if (currentUser == null) {
            return ResponseEntity
                    .notFound().build();
        }

        currentUser.setLastName(user.getLastName());

        users.stream().filter(u -> id.equals(u.getId()))
                .forEach(u -> u.setLastName(user.getLastName()));

        return ResponseEntity.
                ok(currentUser);
    }

    @DeleteMapping(value = "/users/{id}")
    public ResponseEntity<UserDTO> deleteUser(@PathVariable("id") String id) {

        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(id)).findFirst()
                .orElse(null);
        if (currentUser == null) {
            return ResponseEntity
                    .notFound().build();
        }

        users = users.stream().filter(u -> !currentUser.equals(u))
                .collect(Collectors.toList());

        return ResponseEntity.
                ok().build();

    }

    @RequestMapping(value = "/authenticated", method = RequestMethod.HEAD)
    public ResponseEntity<Void> authenticated(HttpServletRequest request) {

        String authHeader = request.getHeader(HttpHeaders.AUTHORIZATION);
        boolean isAuthenticated = StringUtils.isNotBlank(authHeader);
        if (isAuthenticated) {
            return ResponseEntity.ok()
                    .header(HttpHeaders.AUTHORIZATION, authHeader)
                    .build();
        }
        return ResponseEntity.status(401).build();
    }
}
