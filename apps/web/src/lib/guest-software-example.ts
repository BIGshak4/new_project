/** Local walkthrough of the one-line repair. User-provided code is never executed. */
export const starterMaximum = `int maximum(const int a[], int n) {
    int best = 0;
    for (int i = 0; i < n; ++i) {
        if (a[i] > best) best = a[i];
    }
    return best;
}`;

export const fixedMaximum = starterMaximum.replace("int best = 0;", "int best = a[0];");

export type MaximumCase = { input: number[]; expected: number; actual: number | null };
export type MaximumCheck = { supported: false } | { supported: true; correct: boolean; cases: MaximumCase[] };

function tokens(source: string): string[] {
  return source.replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, " ").match(/[A-Za-z_]\w*|\d+|\+\+|[^\s]/g) ?? [];
}
const template = tokens(starterMaximum);
const start = template.indexOf("=") + 1;
const end = template.indexOf(";", start);

/** The surrounding C function stays fixed. Interpret only the editable initializer. */
export function checkMaximumExample(source: string): MaximumCheck {
  if (source.length > 12000) return { supported: false };
  const code = tokens(source);
  const semicolon = code.indexOf(";", start);
  if (semicolon === -1 || template.slice(0, start).join(" ") !== code.slice(0, start).join(" ")
      || template.slice(end).join(" ") !== code.slice(semicolon).join(" ")) return { supported: false };

  const initializer = code.slice(start, semicolon).join(" ");
  let seed: (a: number[]) => number | undefined;
  let additionalCase: number[] | null = null;
  if (initializer === "a [ 0 ]" || initializer === "* a") seed = a => a[0];
  else if (initializer === "a [ n - 1 ]") seed = a => a[a.length - 1];
  else if (/^a \[ (?:0|[1-9]\d*) \]$/.test(initializer)) {
    const index = Number(initializer.split(" ")[2]);
    seed = a => a[index];
  } else if (/^(?:- )?(?:0|[1-9]\d*)$/.test(initializer)) {
    const constant = Number(initializer.replaceAll(" ", ""));
    if (constant < -2147483648 || constant > 2147483647) return { supported: false };
    seed = () => constant;
    if (constant > -2147483648) additionalCase = [constant - 1];
  } else return { supported: false };

  const inputs = [[3, 9, 5], [-8, -3, -5], [-6]];
  if (additionalCase && !inputs.some(a => a.every(n => n < (seed(a) ?? -Infinity)))) inputs.push(additionalCase);
  const cases = inputs.map(input => {
    const initial = seed(input);
    const actual = initial === undefined ? null : input.reduce((best, value) => value > best ? value : best, initial);
    return { input, expected: Math.max(...input), actual };
  });
  return { supported: true, correct: cases.every(test => test.actual === test.expected), cases };
}
