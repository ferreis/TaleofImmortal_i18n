using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace TalesOfMortalI18N
{
    // JSON estrito sem DataContractJsonSerializer, Newtonsoft ou reflexão.
    // Compatível com strings Unicode, escapes, objetos, arrays e números.
    // A implementação usa somente classes fundamentais do .NET 4.x.
    internal static class JsonTextParser
    {
        internal static Dictionary<string, object> ParseObject(string input)
        {
            var reader = new Reader(input);
            object value = reader.Value(0);
            reader.WhiteSpace();
            if (!reader.AtEnd)
                throw reader.Error("Dados adicionais após o documento JSON.");

            var obj = value as Dictionary<string, object>;
            if (obj == null)
                throw reader.Error("A raiz do JSON deve ser um objeto.");
            return obj;
        }

        private sealed class Reader
        {
            private readonly string text;
            private int pos;

            internal Reader(string input)
            {
                if (input == null)
                    throw new ArgumentNullException("input");
                text = input;
            }

            internal bool AtEnd { get { return pos >= text.Length; } }

            internal FormatException Error(string message)
            {
                return new FormatException(message + " (caractere " + pos + ").");
            }

            internal void WhiteSpace()
            {
                while (!AtEnd)
                {
                    char ch = text[pos];
                    if (ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n' ||
                        (pos == 0 && ch == '\uFEFF'))
                        pos++;
                    else
                        break;
                }
            }

            private char Peek()
            {
                if (AtEnd) throw Error("Fim inesperado do JSON.");
                return text[pos];
            }

            private bool Take(char expected)
            {
                WhiteSpace();
                if (!AtEnd && text[pos] == expected)
                {
                    pos++;
                    return true;
                }
                return false;
            }

            private void Expect(char expected)
            {
                if (!Take(expected))
                    throw Error("Esperado '" + expected + "'.");
            }

            internal object Value(int depth)
            {
                if (depth > 64)
                    throw Error("JSON excede profundidade máxima.");
                WhiteSpace();
                char ch = Peek();
                if (ch == '{') return Object(depth + 1);
                if (ch == '[') return Array(depth + 1);
                if (ch == '"') return Quoted();
                if (ch == 't') { Literal("true"); return true; }
                if (ch == 'f') { Literal("false"); return false; }
                if (ch == 'n') { Literal("null"); return null; }
                if (ch == '-' || (ch >= '0' && ch <= '9')) return Number();
                throw Error("Valor JSON inválido.");
            }

            private void Literal(string literal)
            {
                if (pos + literal.Length > text.Length ||
                    string.CompareOrdinal(text, pos, literal, 0, literal.Length) != 0)
                    throw Error("Literal JSON inválido.");
                pos += literal.Length;
            }

            private Dictionary<string, object> Object(int depth)
            {
                Expect('{');
                var values = new Dictionary<string, object>(StringComparer.Ordinal);
                if (Take('}')) return values;

                do
                {
                    WhiteSpace();
                    if (Peek() != '"') throw Error("Chave JSON deve ser texto.");
                    string name = Quoted();
                    Expect(':');
                    object value = Value(depth);
                    if (values.ContainsKey(name))
                        throw Error("Chave repetida no JSON: " + name);
                    values.Add(name, value);
                    if (Take('}')) return values;
                    Expect(',');
                }
                while (true);
            }

            private List<object> Array(int depth)
            {
                Expect('[');
                var values = new List<object>();
                if (Take(']')) return values;

                do
                {
                    values.Add(Value(depth));
                    if (Take(']')) return values;
                    Expect(',');
                }
                while (true);
            }

            private string Quoted()
            {
                Expect('"');
                int start = pos;
                StringBuilder builder = null;
                while (!AtEnd)
                {
                    char ch = text[pos++];
                    if (ch == '"')
                    {
                        if (builder == null)
                            return text.Substring(start, pos - start - 1);
                        return builder.ToString();
                    }

                    if (ch < 32) throw Error("Caractere de controle não escapado na string.");

                    if (ch != '\\')
                    {
                        if (builder != null) builder.Append(ch);
                        continue;
                    }

                    if (builder == null)
                        builder = new StringBuilder(text.Substring(start, pos - start - 1));
                    if (AtEnd) throw Error("Escape incompleto.");
                    char escape = text[pos++];
                    switch (escape)
                    {
                        case '"': builder.Append('"'); break;
                        case '\\': builder.Append('\\'); break;
                        case '/': builder.Append('/'); break;
                        case 'b': builder.Append('\b'); break;
                        case 'f': builder.Append('\f'); break;
                        case 'n': builder.Append('\n'); break;
                        case 'r': builder.Append('\r'); break;
                        case 't': builder.Append('\t'); break;
                        case 'u': builder.Append((char)Hex4()); break;
                        default: throw Error("Escape JSON inválido: \\" + escape);
                    }
                }
                throw Error("String JSON não terminada.");
            }

            private int Hex4()
            {
                if (pos + 4 > text.Length) throw Error("Escape Unicode incompleto.");
                int value = 0;
                for (int i = 0; i < 4; i++)
                {
                    char ch = text[pos++];
                    int digit = ch >= '0' && ch <= '9' ? ch - '0' :
                        ch >= 'a' && ch <= 'f' ? ch - 'a' + 10 :
                        ch >= 'A' && ch <= 'F' ? ch - 'A' + 10 : -1;
                    if (digit < 0) throw Error("Escape Unicode inválido.");
                    value = (value << 4) | digit;
                }
                return value;
            }

            private object Number()
            {
                int start = pos;
                if (text[pos] == '-') pos++;
                if (AtEnd) throw Error("Número incompleto.");
                if (text[pos] == '0') pos++;
                else
                {
                    if (text[pos] < '1' || text[pos] > '9')
                        throw Error("Número inválido.");
                    Digits();
                }

                if (!AtEnd && text[pos] == '.')
                {
                    pos++;
                    int before = pos;
                    Digits();
                    if (pos == before) throw Error("Fração incompleta.");
                }
                if (!AtEnd && (text[pos] == 'e' || text[pos] == 'E'))
                {
                    pos++;
                    if (!AtEnd && (text[pos] == '-' || text[pos] == '+')) pos++;
                    int before = pos;
                    Digits();
                    if (pos == before) throw Error("Expoente incompleto.");
                }

                double parsed;
                if (!double.TryParse(text.Substring(start, pos - start),
                    NumberStyles.Float, CultureInfo.InvariantCulture, out parsed) ||
                    double.IsInfinity(parsed) || double.IsNaN(parsed))
                    throw Error("Número fora do intervalo.");
                return parsed;
            }

            private void Digits()
            {
                while (!AtEnd && text[pos] >= '0' && text[pos] <= '9')
                    pos++;
            }
        }
    }
}
