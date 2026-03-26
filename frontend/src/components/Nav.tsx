import Link from "next/link";

export default function Nav() {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center gap-8 px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="text-xl font-bold text-gray-900">
          StartupTracker
        </Link>
        <div className="flex gap-6">
          <Link
            href="/"
            className="text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            Companies
          </Link>
          <Link
            href="/funding-rounds"
            className="text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            Funding Rounds
          </Link>
        </div>
      </div>
    </nav>
  );
}
