import Link from 'next/link';
import {
  Facebook,
  Twitter,
  Instagram,
  Linkedin,
  Mail,
  Phone,
  MapPin,
} from 'lucide-react';

const footerLinks = {
  marketplace: [
    { label: 'Toutes les annonces', href: '/annonces' },
    { label: 'Catégories', href: '/categories' },
    { label: 'Vendre', href: '/annonces/creer' },
    { label: 'Comment ça marche', href: '/comment-ca-marche' },
  ],
  vendeurs: [
    { label: 'Espace vendeur', href: '/dashboard' },
    { label: 'Abonnements Pro', href: '/abonnements' },
    { label: 'Booster mon annonce', href: '/boost' },
    { label: 'Guide du vendeur', href: '/guide-vendeur' },
  ],
  aide: [
    { label: 'Centre d\'aide', href: '/aide' },
    { label: 'FAQ', href: '/faq' },
    { label: 'Contact', href: '/contact' },
    { label: 'Signaler un problème', href: '/signaler' },
  ],
  legal: [
    { label: 'Conditions d\'utilisation', href: '/conditions' },
    { label: 'Politique de confidentialité', href: '/confidentialite' },
    { label: 'Mentions légales', href: '/mentions-legales' },
    { label: 'Cookies', href: '/cookies' },
  ],
};

export function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      {/* Main Footer */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center space-x-2 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-2xl">V</span>
              </div>
              <span className="font-bold text-2xl text-white">Vyzio</span>
            </Link>
            <p className="text-sm text-gray-400 mb-4">
              La marketplace d'annonces pour acheter et vendre en toute simplicité.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Marketplace */}
          <div>
            <h3 className="font-semibold text-white mb-4">Marketplace</h3>
            <ul className="space-y-2">
              {footerLinks.marketplace.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-gray-400 hover:text-white transition-colors text-sm">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Vendeurs */}
          <div>
            <h3 className="font-semibold text-white mb-4">Vendeurs</h3>
            <ul className="space-y-2">
              {footerLinks.vendeurs.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-gray-400 hover:text-white transition-colors text-sm">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Aide */}
          <div>
            <h3 className="font-semibold text-white mb-4">Aide</h3>
            <ul className="space-y-2">
              {footerLinks.aide.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-gray-400 hover:text-white transition-colors text-sm">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="font-semibold text-white mb-4">Contact</h3>
            <ul className="space-y-3">
              <li className="flex items-center space-x-3 text-sm">
                <Mail className="h-4 w-4 text-primary-500" />
                <span>contact@vyzio.com</span>
              </li>
              <li className="flex items-center space-x-3 text-sm">
                <Phone className="h-4 w-4 text-primary-500" />
                <span>+33 1 23 45 67 89</span>
              </li>
              <li className="flex items-start space-x-3 text-sm">
                <MapPin className="h-4 w-4 text-primary-500 mt-0.5" />
                <span>123 Rue de la Tech<br />75001 Paris, France</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Footer */}
      <div className="border-t border-gray-800">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-500">
              © {new Date().getFullYear()} Vyzio. Tous droits réservés.
            </p>
            <div className="flex space-x-6">
              {footerLinks.legal.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
