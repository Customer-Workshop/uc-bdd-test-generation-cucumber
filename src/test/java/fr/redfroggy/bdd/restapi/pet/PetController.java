package fr.redfroggy.bdd.restapi.pet;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class PetController {

    public static List<PetDTO> pets = new ArrayList<>();

    @GetMapping("/pets")
    public ResponseEntity<List<PetDTO>> getAll(
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "species", required = false) String species,
            @RequestParam(value = "page", required = false, defaultValue = "0") int page,
            @RequestParam(value = "size", required = false, defaultValue = "20") int size) {

        List<PetDTO> filtered = pets;

        if (StringUtils.isNotBlank(status)) {
            filtered = filtered.stream()
                    .filter(p -> status.equalsIgnoreCase(p.getStatus()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(species)) {
            filtered = filtered.stream()
                    .filter(p -> species.equalsIgnoreCase(p.getSpecies()))
                    .collect(Collectors.toList());
        }

        int fromIndex = page * size;
        if (fromIndex >= filtered.size()) {
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                    .header("X-Total-Count", String.valueOf(filtered.size()))
                    .header("X-Page", String.valueOf(page))
                    .header("X-Page-Size", String.valueOf(size))
                    .body(new ArrayList<>());
        }
        int toIndex = Math.min(fromIndex + size, filtered.size());
        List<PetDTO> paged = filtered.subList(fromIndex, toIndex);

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .header("X-Total-Count", String.valueOf(filtered.size()))
                .header("X-Page", String.valueOf(page))
                .header("X-Page-Size", String.valueOf(size))
                .body(paged);
    }

    @GetMapping("/pets/{id}")
    public ResponseEntity<PetDTO> get(@PathVariable("id") String id) {
        PetDTO pet = pets.stream()
                .filter(p -> p.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (pet == null) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(pet);
    }

    @PostMapping(value = "/pets")
    public ResponseEntity<PetDTO> addPet(@RequestBody PetDTO pet) {
        if (pet.getId() == null || pet.getId().trim().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }

        if (pet.getName() == null || pet.getName().trim().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }

        if (pet.getSpecies() == null || pet.getSpecies().trim().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }

        PetDTO existing = pets.stream()
                .filter(p -> pet.getId().equals(p.getId()))
                .findFirst()
                .orElse(null);

        if (existing != null) {
            return ResponseEntity.status(409).build();
        }

        if (pet.getStatus() == null || pet.getStatus().trim().isEmpty()) {
            pet.setStatus("available");
        }

        pets.add(pet);
        return ResponseEntity.status(201)
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(pet);
    }

    @PutMapping(value = "/pets/{id}")
    public ResponseEntity<PetDTO> updatePet(@RequestBody PetDTO pet, @PathVariable String id) {
        PetDTO current = pets.stream()
                .filter(p -> p.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (current == null) {
            return ResponseEntity.notFound().build();
        }

        pets.stream().filter(p -> id.equals(p.getId())).forEach(p -> {
            p.setName(pet.getName());
            p.setSpecies(pet.getSpecies());
            p.setBreed(pet.getBreed());
            p.setAge(pet.getAge());
            p.setStatus(pet.getStatus());
            p.setTags(pet.getTags());
        });

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(pet);
    }

    @PatchMapping(value = "/pets/{id}")
    public ResponseEntity<PetDTO> patchPet(@RequestBody PartialPetDTO pet, @PathVariable String id) {
        PetDTO current = pets.stream()
                .filter(p -> p.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (current == null) {
            return ResponseEntity.notFound().build();
        }

        if (pet.getName() != null) {
            current.setName(pet.getName());
        }
        if (pet.getStatus() != null) {
            current.setStatus(pet.getStatus());
        }

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(current);
    }

    @DeleteMapping(value = "/pets/{id}")
    public ResponseEntity<Void> deletePet(@PathVariable("id") String id) {
        PetDTO current = pets.stream()
                .filter(p -> p.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (current == null) {
            return ResponseEntity.notFound().build();
        }

        pets = pets.stream()
                .filter(p -> !p.getId().equals(id))
                .collect(Collectors.toList());

        return ResponseEntity.ok().build();
    }
}
