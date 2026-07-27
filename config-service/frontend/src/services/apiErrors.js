// Extracts a consistent { fieldErrors, generalError } shape from an axios
// error raised by the API client, so views never end up rendering nothing.
export function extractApiErrors(err) {
  const fieldErrors = {};
  let generalError = null;

  const data = err.response?.data;
  if (data && typeof data === "object" && !Array.isArray(data)) {
    if (typeof data.detail === "string") {
      generalError = data.detail;
    } else if (Array.isArray(data.non_field_errors)) {
      generalError = data.non_field_errors.join(" ");
    }

    for (const [key, value] of Object.entries(data)) {
      if (key === "detail" || key === "non_field_errors") {
        continue;
      }
      fieldErrors[key] = value;
    }
  } else {
    generalError = err.message;
  }

  if (Object.keys(fieldErrors).length === 0 && generalError === null) {
    generalError = err.message;
  }

  return { fieldErrors, generalError };
}
