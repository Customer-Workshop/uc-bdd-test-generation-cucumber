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
import java.util.Comparator;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class UserController {

    private static final int MAX_NAME_LENGTH = 100;
    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$");

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
            String[] sortParts = sort.split(",");
            String sortField = sortParts[0];
            boolean ascending = sortParts.length < 2 || "asc".equalsIgnoreCase(sortParts[1]);

            Comparator<UserDTO> comparator = getUserComparator(sortField);
            if (comparator != null) {
                if (!ascending) {
                    comparator = comparator.reversed();
                }
                result = result.stream().sorted(comparator).collect(Collectors.toList());
            }
        }

        if (page != null && size != null) {
            if (page < 0 || size <= 0) {
                return ResponseEntity.badRequest()
                        .body(Collections.singletonMap("error", "Invalid pagination parameters"));
            }
            int fromIndex = page * size;
            if (fromIndex >= result.size()) {
                Map<String, Object> pageResponse = new LinkedHashMap<>();
                pageResponse.put("content", Collections.emptyList());
                pageResponse.put("page", page);
                pageResponse.put("size", size);
                pageResponse.put("totalElements", result.size());
                pageResponse.put("totalPages", (int) Math.ceil((double) result.size() / size));
                return ResponseEntity.ok(pageResponse);
            }
            int toIndex = Math.min(fromIndex + size, result.size());
            List<UserDTO> pageContent = result.subList(fromIndex, toIndex);

            Map<String, Object> pageResponse = new LinkedHashMap<>();
            pageResponse.put("content", pageContent);
            pageResponse.put("page", page);
            pageResponse.put("size", size);
            pageResponse.put("totalElements", result.size());
            pageResponse.put("totalPages", (int) Math.ceil((double) result.size() / size));
            return ResponseEntity.ok(pageResponse);
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
    public ResponseEntity<?> addUser(@RequestBody UserDTO user) {

        List<String> errors = validateUser(user);
        if (!errors.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("errors", errors));
        }

        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(user.getId())).findFirst()
                .orElse(null);
        if (currentUser != null) {
            return ResponseEntity.status(409)
                    .body(Collections.singletonMap("error", "User with id " + user.getId() + " already exists"));
        }

        users.add(user);
        return ResponseEntity.status(201)
                .body(user);
    }

    @PostMapping(value = "/users", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<List<UserDTO>> uploadFile(@RequestParam(name = "file") MultipartFile file) throws IOException {

        CsvToBean<UserCsvLine> csvBean = new CsvToBeanBuilder<UserCsvLine>(new InputStreamReader(file.getInputStream()))
                .withType(UserCsvLine.class)
                .withIgnoreLeadingWhiteSpace(true)
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
    public ResponseEntity<UserDTO> updateUser(@RequestBody UserDTO user, @PathVariable String id) {

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
    public ResponseEntity<UserDTO> patchUser(@RequestBody PartialUserDTO user, @PathVariable String id) {

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

    private List<String> validateUser(UserDTO user) {
        List<String> errors = new ArrayList<>();

        if (StringUtils.isBlank(user.getId())) {
            errors.add("id is required");
        }
        if (StringUtils.isBlank(user.getFirstName())) {
            errors.add("firstName is required");
        }
        if (StringUtils.isBlank(user.getLastName())) {
            errors.add("lastName is required");
        }
        if (user.getFirstName() != null && user.getFirstName().length() > MAX_NAME_LENGTH) {
            errors.add("firstName must not exceed " + MAX_NAME_LENGTH + " characters");
        }
        if (user.getLastName() != null && user.getLastName().length() > MAX_NAME_LENGTH) {
            errors.add("lastName must not exceed " + MAX_NAME_LENGTH + " characters");
        }
        if (user.getEmail() != null && !EMAIL_PATTERN.matcher(user.getEmail()).matches()) {
            errors.add("email format is invalid");
        }

        return errors;
    }

    private Comparator<UserDTO> getUserComparator(String field) {
        switch (field) {
            case "firstName":
                return Comparator.comparing(UserDTO::getFirstName, String.CASE_INSENSITIVE_ORDER);
            case "lastName":
                return Comparator.comparing(UserDTO::getLastName, String.CASE_INSENSITIVE_ORDER);
            case "age":
                return Comparator.comparingInt(UserDTO::getAge);
            case "id":
                return Comparator.comparing(UserDTO::getId);
            default:
                return null;
        }
    }
}
