package fr.redfroggy.bdd.restapi.support;

import java.util.Comparator;
import java.util.List;
import java.util.Map;

/**
 * Sorting helper for the in memory collections exposed by the test controllers.
 * Expected query parameter format: {@code sort=field[,asc|desc]}.
 */
public final class Sorting {

    private Sorting() {
    }

    /**
     * @return an {@link ApiError} when the sort expression is invalid, null when the list has been sorted.
     */
    public static <T> ApiError sort(List<T> content, String sort, Map<String, Comparator<T>> comparators) {
        if (sort == null || sort.trim().isEmpty()) {
            return null;
        }

        String[] parts = sort.split(",");
        String field = parts[0].trim();
        String direction = parts.length > 1 ? parts[1].trim().toLowerCase() : "asc";

        Comparator<T> comparator = comparators.get(field);
        if (comparator == null) {
            return new ApiError("unknown sort field: " + field + ", expected one of " + comparators.keySet(), "sort");
        }
        if (!"asc".equals(direction) && !"desc".equals(direction)) {
            return new ApiError("unknown sort direction: " + direction + ", expected asc or desc", "sort");
        }

        content.sort("desc".equals(direction) ? comparator.reversed() : comparator);
        return null;
    }
}
