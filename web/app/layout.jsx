import './globals.css';

export const metadata = {
  title: 'SkyCast — Real-Time Weather Intelligence',
  description: 'Next-Generation Weather Dashboard powered by live Open-Meteo REST APIs with 60 FPS HTML5 canvas particle graphics and glassmorphism UI.',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌤️</text></svg>'
  }
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-sky-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
