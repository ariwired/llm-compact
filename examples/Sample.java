package demo;

import java.util.*;
import java.util.function.Function;


@SuppressWarnings("unchecked")
public class Sample<T extends Comparable<T>> {
    private final Map<String, List<Integer>> index = new HashMap<>();
    private static final String BLOCK = """
        line 1
          line 2 with  spaces
        """;

    public static void main(String[] args) {
        int i = 10;
        while (i-- > 0) {
            if (i % 2 == 0 && i != 4) continue;
            System.out.println("i = " + i + " 'aspas' \"escaped\"");
        }
        Function<Integer, Integer> inc = x -> x + 1;
        int neg = - -i;
        long big = 1_000_000L;
        double d = 1e-3 + .5;
        char c = '\'';
        List<List<String>> nested = new ArrayList<>();
        Runnable r = Sample::helper;
        r.run();
    }

    static void helper() {
        int a = 1, b = 2;
        a = a + +b;
        b = a - --b;
    }
}
