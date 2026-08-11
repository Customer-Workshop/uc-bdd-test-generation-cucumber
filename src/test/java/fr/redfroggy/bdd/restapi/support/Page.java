package fr.redfroggy.bdd.restapi.support;

import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;

import java.util.List;

/**
 * Pagination helper: the paginated payload stays a plain json array, pagination metadata is exposed through
 * http headers.
 */
public final class Page {

    public static final String TOTAL_COUNT = "X-Total-Count";

    public static final String PAGE = "X-Page";

    public static final String PAGE_SIZE = "X-Page-Size";

    public static final String TOTAL_PAGES = "X-Total-Pages";

    private static final int DEFAULT_SIZE = 20;

    private Page() {
    }

    public static <T> ResponseEntity<Object> of(List<T> content, Integer page, Integer size) {
        int pageNumber = page == null ? 0 : page;
        int pageSize = size == null ? DEFAULT_SIZE : size;

        int total = content.size();
        int totalPages = pageSize == 0 ? 0 : (int) Math.ceil((double) total / pageSize);
        int from = Math.min(pageNumber * pageSize, total);
        int to = Math.min(from + pageSize, total);

        return ResponseEntity.ok()
                .header(TOTAL_COUNT, String.valueOf(total))
                .header(PAGE, String.valueOf(pageNumber))
                .header(PAGE_SIZE, String.valueOf(pageSize))
                .header(TOTAL_PAGES, String.valueOf(totalPages))
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .body(content.subList(from, to));
    }

    public static ApiError validate(Integer page, Integer size) {
        if (page != null && page < 0) {
            return new ApiError("page must be greater than or equal to 0", "page");
        }
        if (size != null && size < 1) {
            return new ApiError("size must be greater than 0", "size");
        }
        return null;
    }
}
