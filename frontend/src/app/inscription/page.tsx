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
import { Mail, Lock, User, Eye, EyeOff, CheckCircle } from 'lucide-react';

const registerSchema = z.object({
  first_name: z.string().min(2, 'Minimum 2 caractères'),
  last_name: z.string().min(2, 'Minimum 2 caractères'),
  username: z.string().min(3, 'Minimum 3 caractères'),
  email: z.string().email('Email invalide'),
  password: z.string().min(8, 'Minimum 8 caractères'),
  confirmPassword: z.string(),
  role: z.enum(['buyer', 'seller']),
  acceptTerms: z.boolean().refine(val => val === true, 'Vous devez accepter les conditions'),
}).refine(data => data.password === data.confirmPassword, {
  message: 'Les mots de passe ne correspondent pas',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      role: 'buyer',
    },
  });

  const selectedRole = watch('role');
  const password = watch('password', '');

  const passwordStrength = {
    hasLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
  };

  const onSubmit = async (data: RegisterForm) => {
    try {
      await registerUser({
        email: data.email,
        username: data.username,
        first_name: data.first_name,
        last_name: data.last_name,
        password: data.password,
        password2: data.confirmPassword,
        role: data.role,
      });
      toast({
        title: 'Compte créé !',
        description: 'Bienvenue sur Vyzio !',
        variant: 'success',
      });
      router.push('/dashboard');
    } catch (error: any) {
      const errorData = error.response?.data;
      let errorMessage = 'Une erreur est survenue';
      
      if (errorData) {
        const firstError = Object.values(errorData)[0];
        if (Array.isArray(firstError)) {
          errorMessage = firstError[0] as string;
        } else if (typeof firstError === 'string') {
          errorMessage = firstError;
        }
      }
      
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Image */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary-600 to-purple-700 items-center justify-center p-12">
        <div className="max-w-lg text-white">
          <h2 className="text-4xl font-bold mb-6">
            Rejoignez la communauté Vyzio
          </h2>
          <p className="text-xl text-white/80 mb-8">
            Créez votre compte en quelques minutes et commencez à acheter ou vendre.
          </p>
          <ul className="space-y-4">
            <li className="flex items-center">
              <CheckCircle className="h-6 w-6 text-green-400 mr-3" />
              <span>Inscription 100% gratuite</span>
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-6 w-6 text-green-400 mr-3" />
              <span>Publication d'annonces illimitées</span>
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-6 w-6 text-green-400 mr-3" />
              <span>Messagerie sécurisée</span>
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-6 w-6 text-green-400 mr-3" />
              <span>Support réactif 7j/7</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
        <div className="w-full max-w-md">
          <Link href="/" className="flex items-center space-x-2 mb-8">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-2xl">V</span>
            </div>
            <span className="font-bold text-2xl bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
              Vyzio
            </span>
          </Link>

          <h1 className="text-3xl font-bold text-gray-900 mb-2">Créer un compte</h1>
          <p className="text-gray-600 mb-8">
            Remplissez le formulaire pour vous inscrire
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Role Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Je souhaite...
              </label>
              <div className="grid grid-cols-2 gap-4">
                <label className={`
                  flex items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all
                  ${selectedRole === 'buyer' 
                    ? 'border-primary-500 bg-primary-50 text-primary-700' 
                    : 'border-gray-200 hover:border-gray-300'}
                `}>
                  <input
                    type="radio"
                    value="buyer"
                    {...register('role')}
                    className="sr-only"
                  />
                  <div className="text-center">
                    <span className="font-medium">Acheter</span>
                    <p className="text-xs text-gray-500 mt-1">Trouver des annonces</p>
                  </div>
                </label>
                <label className={`
                  flex items-center justify-center p-4 rounded-xl border-2 cursor-pointer transition-all
                  ${selectedRole === 'seller' 
                    ? 'border-primary-500 bg-primary-50 text-primary-700' 
                    : 'border-gray-200 hover:border-gray-300'}
                `}>
                  <input
                    type="radio"
                    value="seller"
                    {...register('role')}
                    className="sr-only"
                  />
                  <div className="text-center">
                    <span className="font-medium">Vendre</span>
                    <p className="text-xs text-gray-500 mt-1">Publier des annonces</p>
                  </div>
                </label>
              </div>
            </div>

            {/* Prénom et Nom */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Prénom
                </label>
                <Input
                  type="text"
                  placeholder="Jean"
                  error={errors.first_name?.message}
                  {...register('first_name')}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Nom
                </label>
                <Input
                  type="text"
                  placeholder="Dupont"
                  error={errors.last_name?.message}
                  {...register('last_name')}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Nom d'utilisateur
              </label>
              <Input
                type="text"
                placeholder="johndoe"
                icon={<User className="h-5 w-5" />}
                error={errors.username?.message}
                {...register('username')}
              />
            </div>

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
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {/* Password Strength */}
              {password && (
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  <span className={passwordStrength.hasLength ? 'text-green-600' : 'text-gray-400'}>
                    ✓ 8 caractères min.
                  </span>
                  <span className={passwordStrength.hasUppercase ? 'text-green-600' : 'text-gray-400'}>
                    ✓ Une majuscule
                  </span>
                  <span className={passwordStrength.hasLowercase ? 'text-green-600' : 'text-gray-400'}>
                    ✓ Une minuscule
                  </span>
                  <span className={passwordStrength.hasNumber ? 'text-green-600' : 'text-gray-400'}>
                    ✓ Un chiffre
                  </span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Confirmer le mot de passe
              </label>
              <Input
                type="password"
                placeholder="••••••••"
                icon={<Lock className="h-5 w-5" />}
                error={errors.confirmPassword?.message}
                {...register('confirmPassword')}
              />
            </div>

            <div>
              <label className="flex items-start">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mt-1"
                  {...register('acceptTerms')}
                />
                <span className="ml-2 text-sm text-gray-600">
                  J'accepte les{' '}
                  <Link href="/conditions" className="text-primary-600 hover:underline">
                    conditions d'utilisation
                  </Link>{' '}
                  et la{' '}
                  <Link href="/confidentialite" className="text-primary-600 hover:underline">
                    politique de confidentialité
                  </Link>
                </span>
              </label>
              {errors.acceptTerms && (
                <p className="text-sm text-red-500 mt-1">{errors.acceptTerms.message}</p>
              )}
            </div>

            <Button type="submit" variant="gradient" size="xl" className="w-full" loading={isLoading}>
              Créer mon compte
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Déjà un compte ?{' '}
            <Link href="/connexion" className="text-primary-600 hover:underline font-medium">
              Se connecter
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
