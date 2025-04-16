export function filterProducts(products, filters) {
  // Separate dietary and vegetable type filters
  const dietaryFilters = {
    vegan: filters.vegan,
    glutenFree: filters.glutenFree,
    nutFree: filters.nutFree,
    organic: filters.organic,
    nonGMO: filters.nonGMO,
    lowCarb: filters.lowCarb,
    highFiber: filters.highFiber,
    lowSodium: filters.lowSodium,
  };

  const vegTypeFilters = {
    root: filters.root,
    leafy: filters.leafy,
    fruitVegetable: filters.fruitVegetable,
    cruciferous: filters.cruciferous,
    bulb: filters.bulb,
    squash: filters.squash,
    stem: filters.stem,
    other: filters.other,
  };

  return products.filter((product) => {
    // Dietary filter logic (match all selected dietary filters)
    const matchesDietary = Object.entries(dietaryFilters).every(([key, value]) =>
      !value || product.tags.includes(key.toLowerCase().replace("glutenFree", "gluten-free").replace("nonGMO", "non-gmo"))
    );

    // Vegetable type filter logic (match any selected vegetable type)
    const matchesVegType = Object.keys(vegTypeFilters).some((key) => {
      if (!vegTypeFilters[key]) return false;
      const filterKey = key.toLowerCase() === "fruitvegetable" ? "fruit_vegetable" : key.toLowerCase();
      return product.vegType === filterKey;
    }) || Object.values(vegTypeFilters).every((value) => !value); // If no veg type filters are selected, include all products

    return matchesDietary && matchesVegType;
  });
}