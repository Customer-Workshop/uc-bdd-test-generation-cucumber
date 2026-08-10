package fr.redfroggy.bdd.restapi.support;

import fr.redfroggy.bdd.restapi.error.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Sorting and pagination shared by the sample controllers.
 */
public final class PageSupport {

    public static final int MAX_PAGE_SIZE = 100;

    private PageSupport() {
    }

    public static <T> List<T> sort(List<T> items, String sort, String order, Map<String, Comparator<T>> comparators) {
        if (!StringUtils.hasText(sort)) {
            if (StringUtils.hasText(order)) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "order requires a sort field");
            }
            return items;
        }

        Comparator<T> comparator = comparators.get(sort);
        if (comparator == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Unknown sort field: " + sort);
        }

        if (StringUtils.hasText(order)) {
            if ("desc".equalsIgnoreCase(order)) {
                comparator = comparator.reversed();
            } else if (!"asc".equalsIgnoreCase(order)) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "Unknown sort order: " + order);
            }
        }

        return items.stream().sorted(comparator).collect(Collectors.toList());
    }

    public static <T> List<T> paginate(List<T> items, Integer page, Integer size) {
        if (page == null && size == null) {
            return items;
        }

        int pageNumber = page == null ? 0 : page;
        int pageSize = size == null ? MAX_PAGE_SIZE : size;

        if (pageNumber < 0) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "page cannot be negative");
        }
        if (pageSize < 1 || pageSize > MAX_PAGE_SIZE) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "size has to be between 1 and " + MAX_PAGE_SIZE);
        }

        int from = (int) Math.min((long) pageNumber * pageSize, items.size());
        int to = Math.min(from + pageSize, items.size());

        return new ArrayList<>(items.subList(from, to));
    }
}
