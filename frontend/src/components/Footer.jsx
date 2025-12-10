export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="container mx-auto px-6 py-6">
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-2">
            © {new Date().getFullYear()} <span className="font-semibold text-gray-900">Bugbust3r</span>. All rights reserved.
          </p>
          <div className="flex justify-center items-center space-x-4 text-xs text-gray-500">
            <span>🔒 Secure</span>
            <span>•</span>
            <span>⚡ Fast</span>
            <span>•</span>
            <span>🎯 Accurate</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
