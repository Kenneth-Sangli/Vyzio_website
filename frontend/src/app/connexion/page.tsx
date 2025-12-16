'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/hooks/use-toast';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      await login(data.email, data.password);
      toast({
        title: 'Connexion réussie',
        description: 'Bienvenue sur Vyzio !',
        variant: 'success',
      });
      router.push('/dashboard');
    } catch (error: any) {
      toast({
        title: 'Erreur de connexion',
        description: error.response?.data?.detail || 'Email ou mot de passe incorrect',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <Link href="/" className="flex items-center space-x-2 mb-8">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-2xl">V</span>
            </div>
            <span className="font-bold text-2xl bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
              Vyzio
            </span>
          </Link>

          <h1 className="text-3xl font-bold text-gray-900 mb-2">Connexion</h1>
          <p className="text-gray-600 mb-8">
            Connectez-vous pour accéder à votre compte
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email
              </label>
              <Input
                type="email"
                placeholder="votre@email.com"
                icon={<Mail className="h-5 w-5" />}
                error={errors.email?.message}
                {...register('email')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Mot de passe
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  icon={<Lock className="h-5 w-5" />}
                  error={errors.password?.message}
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                <span className="ml-2 text-sm text-gray-600">Se souvenir de moi</span>
              </label>
              <Link href="/mot-de-passe-oublie" className="text-sm text-primary-600 hover:underline">
                Mot de passe oublié ?
              </Link>
            </div>

            <Button type="submit" variant="gradient" size="xl" className="w-full" loading={isLoading}>
              Se connecter
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Pas encore de compte ?{' '}
            <Link href="/inscription" className="text-primary-600 hover:underline font-medium">
              S'inscrire
            </Link>
          </div>
        </div>
      </div>

      {/* Right Side - Image */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary-600 to-purple-700 items-center justify-center p-12">
        <div className="max-w-lg text-white text-center">
          <h2 className="text-4xl font-bold mb-6">
            Bienvenue sur Vyzio
          </h2>
          <p className="text-xl text-white/80 mb-8">
            La marketplace qui connecte acheteurs et vendeurs en toute simplicité.
          </p>
          <div className="grid grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold">50K+</div>
              <div className="text-white/60 text-sm">Annonces</div>
            </div>
            <div>
              <div className="text-3xl font-bold">100K+</div>
              <div className="text-white/60 text-sm">Utilisateurs</div>
            </div>
            <div>
              <div className="text-3xl font-bold">4.8</div>
              <div className="text-white/60 text-sm">Note</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
