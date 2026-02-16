// This is a function to get the FamilyTitle from the API and return it in data.name
export async function getFamilyTitle(baseUrl: string): Promise<string> {
    const apiUrl = new URL('/api/config/name', baseUrl);
    const response = await fetch(apiUrl);
    const data = await response.json();
    return data.name
}