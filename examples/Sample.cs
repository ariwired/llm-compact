using System;
using System.Collections.Generic;

#nullable enable
namespace Demo
{
    public class Sample
    {
        private readonly Dictionary<string, List<int>> _index = new();
        private const string Path = @"C:\dir\file  with  spaces.txt";

        public static void Main(string[] args)
        {
            int i = 10;
            var name = "world";
            string msg = $"hello {name}, i = {i}";
            string? maybe = null;
            var len = maybe?.Length ?? 0;
            int @class = 3;
            var range = new[] { 1, 2, 3, 4 }[1..^1];
            Func<int, int> inc = x => x + 1;
            int neg = - -i;
            if (i is not 0 && len >= 0)
            {
                Console.WriteLine(msg + @"verbatim ""with quotes""");
            }
            var raw = """
                raw   text
                """;
        }
    }
}
