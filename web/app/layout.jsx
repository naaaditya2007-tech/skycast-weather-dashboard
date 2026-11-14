import { Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
});

export const metadata = {
  title: 'SkyCast — Live Weather & Forecast',
  description: 'Real-time weather intelligence powered by Open-Meteo with atmospheric glassmorphic design.',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌤️</text></svg>'
  }
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`dark ${plusJakartaSans.variable}`}>
      <body className={`${plusJakartaSans.className} bg-slate-950 text-slate-100 antialiased font-sans selection:bg-sky-500 selection:text-white`}>
        {children}
      </body>
    </html>
  );
}
