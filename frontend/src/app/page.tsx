import Link from 'next/link';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  Smartphone,
  Laptop,
  Car,
  Home,
  Shirt,
  Gamepad2,
  Camera,
  Wrench,
  ArrowRight,
  Shield,
  Zap,
  Users,
  Star,
  TrendingUp,
  CheckCircle,
} from 'lucide-react';

const categories = [
  { name: 'Électronique', icon: Smartphone, href: '/annonces?category=electronique', color: 'bg-blue-100 text-blue-600' },
  { name: 'Informatique', icon: Laptop, href: '/annonces?category=informatique', color: 'bg-purple-100 text-purple-600' },
  { name: 'Véhicules', icon: Car, href: '/annonces?category=vehicules', color: 'bg-green-100 text-green-600' },
  { name: 'Immobilier', icon: Home, href: '/annonces?category=immobilier', color: 'bg-yellow-100 text-yellow-600' },
  { name: 'Mode', icon: Shirt, href: '/annonces?category=mode', color: 'bg-pink-100 text-pink-600' },
  { name: 'Jeux & Loisirs', icon: Gamepad2, href: '/annonces?category=jeux-loisirs', color: 'bg-red-100 text-red-600' },
  { name: 'Photo & Vidéo', icon: Camera, href: '/annonces?category=photo-video', color: 'bg-indigo-100 text-indigo-600' },
  { name: 'Services', icon: Wrench, href: '/annonces?category=services', color: 'bg-orange-100 text-orange-600' },
];

const features = [
  {
    icon: Shield,
    title: 'Transactions sécurisées',
    description: 'Paiements protégés et messagerie sécurisée entre acheteurs et vendeurs.',
  },
  {
    icon: Zap,
    title: 'Publication rapide',
    description: 'Créez et publiez votre annonce en moins de 2 minutes.',
  },
  {
    icon: Users,
    title: 'Communauté de confiance',
    description: 'Avis vérifiés et profils authentifiés pour des échanges sereins.',
  },
  {
    icon: TrendingUp,
    title: 'Visibilité maximale',
    description: 'Boostez vos annonces pour toucher plus d\'acheteurs potentiels.',
  },
];

const stats = [
  { value: '50K+', label: 'Annonces actives' },
  { value: '100K+', label: 'Utilisateurs' },
  { value: '4.8/5', label: 'Note moyenne' },
  { value: '95%', label: 'Satisfaction' },
];

const testimonials = [
  {
    content: 'J\'ai vendu mon MacBook en moins de 24h grâce à Vyzio. Interface claire et acheteurs sérieux !',
    author: 'Marie L.',
    role: 'Vendeuse particulière',
    rating: 5,
  },
  {
    content: 'En tant que vendeur pro, l\'abonnement Pro me permet de gérer facilement mes 200+ annonces.',
    author: 'Thomas D.',
    role: 'Vendeur professionnel',
    rating: 5,
  },
  {
    content: 'Super plateforme pour trouver des bonnes affaires. La messagerie intégrée est très pratique.',
    author: 'Sophie M.',
    role: 'Acheteuse régulière',
    rating: 5,
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-purple-700 text-white overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0" style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            }} />
          </div>

          <div className="container mx-auto px-4 py-20 md:py-28 relative">
            <div className="max-w-3xl mx-auto text-center">
              <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
                Achetez et vendez
                <span className="block text-yellow-300">en toute simplicité</span>
              </h1>
              <p className="text-xl md:text-2xl text-white/80 mb-8">
                Des milliers d'annonces vous attendent. Trouvez la perle rare ou vendez ce dont vous n'avez plus besoin.
              </p>

              {/* Search Bar */}
              <div className="bg-white rounded-2xl p-2 shadow-2xl max-w-2xl mx-auto">
                <form action="/annonces" method="GET" className="flex flex-col md:flex-row gap-2">
                  <div className="flex-1 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      name="q"
                      placeholder="Que recherchez-vous ?"
                      className="w-full pl-12 pr-4 py-3 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <Button type="submit" variant="gradient" size="xl" className="md:w-auto">
                    Rechercher
                  </Button>
                </form>
              </div>

              {/* Quick Links */}
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <span className="text-white/60 text-sm">Populaire :</span>
                {['iPhone', 'Vélo', 'PS5', 'Appartement'].map((term) => (
                  <Link
                    key={term}
                    href={`/annonces?q=${term}`}
                    className="text-sm text-white/80 hover:text-white bg-white/10 hover:bg-white/20 px-3 py-1 rounded-full transition-colors"
                  >
                    {term}
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Wave */}
          <div className="absolute bottom-0 left-0 right-0">
            <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M0 120L60 105C120 90 240 60 360 45C480 30 600 30 720 37.5C840 45 960 60 1080 67.5C1200 75 1320 75 1380 75L1440 75V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="white"/>
            </svg>
          </div>
        </section>

        {/* Categories Section */}
        <section className="py-16">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Parcourir par catégorie</h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Explorez nos différentes catégories et trouvez exactement ce que vous cherchez.
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {categories.map((category) => (
                <Link
                  key={category.name}
                  href={category.href}
                  className="group flex flex-col items-center p-6 bg-white rounded-2xl border border-gray-100 hover:border-primary-200 hover:shadow-lg transition-all duration-300"
                >
                  <div className={`p-4 rounded-2xl ${category.color} mb-4 group-hover:scale-110 transition-transform`}>
                    <category.icon className="h-8 w-8" />
                  </div>
                  <span className="font-medium text-gray-900 group-hover:text-primary-600 transition-colors">
                    {category.name}
                  </span>
                </Link>
              ))}
            </div>

            <div className="text-center mt-8">
              <Link href="/annonces">
                <Button variant="outline" size="lg">
                  Voir toutes les catégories
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Pourquoi choisir Vyzio ?</h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Une plateforme conçue pour rendre l'achat et la vente simples, sûrs et efficaces.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature) => (
                <div key={feature.title} className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-600 text-sm">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 bg-gradient-to-r from-primary-600 to-purple-600 text-white">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              {stats.map((stat) => (
                <div key={stat.label}>
                  <div className="text-4xl md:text-5xl font-bold mb-2">{stat.value}</div>
                  <div className="text-white/80">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="py-16">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Ce que disent nos utilisateurs</h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Rejoignez des milliers d'utilisateurs satisfaits qui font confiance à Vyzio.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {testimonials.map((testimonial, index) => (
                <div key={index} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <div className="flex mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                    ))}
                  </div>
                  <p className="text-gray-700 mb-4">"{testimonial.content}"</p>
                  <div>
                    <p className="font-semibold text-gray-900">{testimonial.author}</p>
                    <p className="text-sm text-gray-500">{testimonial.role}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-gray-900 text-white">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Prêt à commencer ?
            </h2>
            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Inscrivez-vous gratuitement et commencez à vendre ou acheter dès aujourd'hui.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/inscription">
                <Button variant="gradient" size="xl">
                  Créer un compte gratuit
                </Button>
              </Link>
              <Link href="/annonces">
                <Button variant="outline" size="xl" className="border-white text-white hover:bg-white hover:text-gray-900">
                  Parcourir les annonces
                </Button>
              </Link>
            </div>

            <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-400">
              <span className="flex items-center">
                <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                Inscription gratuite
              </span>
              <span className="flex items-center">
                <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                Sans engagement
              </span>
              <span className="flex items-center">
                <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                Support 7j/7
              </span>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
