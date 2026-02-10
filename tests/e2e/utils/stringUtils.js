/**
 * Returns a random String of provided length size
 */
export const getRandomString = (length) => {
  if (typeof length !== "number" || !Number.isInteger(length) || length <= 0) {
    throw new Error("Length must be a positive integer");
  }

  const characters = "abcdefghijklmnopqrstuvwxyz";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
};
// ------------------------------------------------------------------------------------------

/**
 * Returns a random item from an array
 */
export const getRandomValue = (array) => {
  if (!Array.isArray(array) || array.length === 0) {
    throw new Error("getRandomValue: input must be a non-empty array");
  }
  const randomIndex = Math.floor(Math.random() * array.length);
  return array[randomIndex];
};
