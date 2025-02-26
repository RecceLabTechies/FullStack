import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">Recce Labs</h1>
          <Link href="/login">
            <Button>Login</Button>
          </Link>
        </div>
      </header>

      <main className="flex-grow">
        <section className="bg-gray-50 py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
                Welcome to Recce Labs
              </h2>
              <p className="mx-auto mt-5 max-w-xl text-xl text-gray-500">
                Empowering your reconnaissance with cutting-edge technology and
                insights.
              </p>
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <h2 className="mb-8 text-3xl font-extrabold text-gray-900">
              Our Features
            </h2>
            <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="rounded-lg bg-white p-6 shadow">
                  <div className="mb-4 h-40 w-full rounded-lg bg-gray-200"></div>
                  <h3 className="mb-2 text-xl font-semibold text-gray-900">
                    Feature {i}
                  </h3>
                  <p className="text-gray-600">
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed
                    do eiusmod tempor incididunt ut labore et dolore magna
                    aliqua.
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-gray-50 py-20">
          <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
            <h2 className="mb-4 text-3xl font-extrabold text-gray-900">
              Ready to get started?
            </h2>
            <p className="mb-8 text-xl text-gray-600">
              Join Recce Labs today and transform your reconnaissance
              capabilities.
            </p>
            <Link href="/login">
              <Button size="lg">Get Started</Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="bg-gray-800 py-12 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div>
              <h3 className="mb-4 text-lg font-semibold">About Us</h3>
              <p className="text-gray-400">
                Recce Labs is dedicated to providing top-notch reconnaissance
                solutions for businesses and organizations.
              </p>
            </div>
            <div>
              <h3 className="mb-4 text-lg font-semibold">Contact</h3>
              <p className="text-gray-400">
                Email: info@reccelabs.com
                <br />
                Phone: (123) 456-7890
              </p>
            </div>
            <div>
              <h3 className="mb-4 text-lg font-semibold">Follow Us</h3>
              <div className="flex space-x-4">
                <a href="#" className="text-gray-400 hover:text-white">
                  Twitter
                </a>
                <a href="#" className="text-gray-400 hover:text-white">
                  LinkedIn
                </a>
                <a href="#" className="text-gray-400 hover:text-white">
                  Facebook
                </a>
              </div>
            </div>
          </div>
          <div className="mt-8 border-t border-gray-700 pt-8 text-center text-gray-400">
            <p>&copy; 2023 Recce Labs. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
