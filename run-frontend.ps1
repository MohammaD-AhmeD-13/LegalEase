Set-Location "D:\University\8th Semester\FYP-II\Project Files\LegalEase\frontend"
if (-not (Test-Path -Path "node_modules")) {
  npm install
}
$env:VITE_API_BASE_URL="http://localhost:8005"
npm run dev
