import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Ultimate Personal Fantasy Football Manager',
  description: 'Your personal fantasy football management system for dominating ESPN and Yahoo leagues',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          <header className="bg-primary text-primary-foreground py-4">
            <div className="container mx-auto px-4">
              <h1 className="font-bold text-2xl">Fantasy Football Manager</h1>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="bg-muted py-6">
            <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} Ultimate Personal Fantasy Football Manager
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
} 