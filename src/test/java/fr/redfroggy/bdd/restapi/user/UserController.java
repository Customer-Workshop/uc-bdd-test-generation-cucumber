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

@RestController
@RequestMapping("/api")
public final class UserController {

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
            Comparator<UserDTO> comparator;
            String field = sort;
            boolean descending = false;

            if (sort.startsWith("-")) {
                field = sort.substring(1);
                descending = true;
            }

            switch (field) {
                case "firstName":
                    comparator = Comparator.comparing(UserDTO::getFirstName, Comparator.nullsLast(String::compareToIgnoreCase));
                    break;
                case "lastName":
                    comparator = Comparator.comparing(UserDTO::getLastName, Comparator.nullsLast(String::compareToIgnoreCase));
                    break;
                case "age":
                    comparator = Comparator.comparingInt(UserDTO::getAge);
                    break;
                default:
                    comparator = Comparator.comparing(UserDTO::getId, Comparator.nullsLast(String::compareTo));
                    break;
            }

            if (descending) {
                comparator = comparator.reversed();
            }
            result = result.stream().sorted(comparator).collect(Collectors.toList());
        }

        if (page != null && size != null) {
            int fromIndex = page * size;
            int toIndex = Math.min(fromIndex + size, result.size());

            int totalElements = result.size();
            int totalPages = (int) Math.ceil((double) totalElements / size);

            if (fromIndex >= result.size()) {
                result = Collections.emptyList();
            } else {
                result = result.subList(fromIndex, toIndex);
            }

            Map<String, Object> pagedResponse = new LinkedHashMap<>();
            pagedResponse.put("content", result);
            pagedResponse.put("page", page);
            pagedResponse.put("size", size);
            pagedResponse.put("totalElements", totalElements);
            pagedResponse.put("totalPages", totalPages);
            return ResponseEntity.ok(pagedResponse);
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

        Map<String, String> errors = new LinkedHashMap<>();

        if (StringUtils.isBlank(user.getId())) {
            errors.put("id", "id is required");
        }
        if (StringUtils.isBlank(user.getFirstName())) {
            errors.put("firstName", "firstName is required");
        }
        if (StringUtils.isBlank(user.getLastName())) {
            errors.put("lastName", "lastName is required");
        }

        if (!errors.isEmpty()) {
            Map<String, Object> errorResponse = new LinkedHashMap<>();
            errorResponse.put("status", 400);
            errorResponse.put("error", "Bad Request");
            errorResponse.put("errors", errors);
            return ResponseEntity.badRequest().body(errorResponse);
        }

        UserDTO currentUser = users.stream().filter(u -> u.getId()
                .equals(user.getId())).findFirst()
                .orElse(null);
        if (currentUser == null) {
            users.add(user);
            return ResponseEntity.status(201)
                    .body(user);
        }

        Map<String, Object> conflictResponse = new LinkedHashMap<>();
        conflictResponse.put("status", 409);
        conflictResponse.put("error", "Conflict");
        conflictResponse.put("message", "User with id " + user.getId() + " already exists");
        return ResponseEntity.status(409).body(conflictResponse);
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
