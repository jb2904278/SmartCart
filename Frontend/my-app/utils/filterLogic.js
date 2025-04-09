export function filterProducts(products, filters) {
    return products.filter((product) =>
      Object.entries(filters).every(([key, value]) =>
        !value || product.tags.includes(key.toLowerCase().replace("glutenfree", "gluten-free"))
      )
    );
  }