package com.trading.investright;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(properties = {
        "investright.api-key=test-key",
        "investright.api-secret=test-secret",
        "investright.base-url=http://localhost:8080",
        "tesseract.data-path=/tmp/tessdata"
})
class InvestRightApplicationTests {

    @Test
    void contextLoads() {
    }
}
