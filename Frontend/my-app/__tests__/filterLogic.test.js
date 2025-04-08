
import { filterProducts } from "../utils/filterLogic";

const products = [
  { name: "Tomato", tags: ["vegan", "gluten-free"] },
  { name: "Bread", tags: ["vegan"] },
  { name: "Chicken", tags: [] }
];

test("filters vegan products", () => {
  const result = filterProducts(products, { vegan: true });
  expect(result).toEqual([
    { name: "Tomato", tags: ["vegan", "gluten-free"] },
    { name: "Bread", tags: ["vegan"] }
  ]);
});

test("filters vegan and gluten-free", () => {
  const result = filterProducts(products, { vegan: true, glutenFree: true });
  expect(result).toEqual([{ name: "Tomato", tags: ["vegan", "gluten-free"] }]);
});

test("returns no results when no match", () => {
  const result = filterProducts(products, { nutFree: true });
  expect(result).toEqual([]);
});
