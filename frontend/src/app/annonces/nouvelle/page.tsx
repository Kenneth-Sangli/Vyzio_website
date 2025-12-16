'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { listingsAPI, categoriesAPI, type Category } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from '@/hooks/use-toast';
import {
  Upload,
  X,
  ImageIcon,
  MapPin,
  DollarSign,
  Tag,
  FileText,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  Info,
} from 'lucide-react';

interface FormData {
  title: string;
  description: string;
  price: string;
  category_id: string;
  condition: string;
  location: string;
  listing_type: string;
}

interface UploadedImage {
  file: File;
  preview: string;
}

export default function CreateListingPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    price: '',
    category_id: '',
    condition: 'good',
    location: '',
    listing_type: 'product',
  });
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [canPublish, setCanPublish] = useState<boolean | null>(null);
  const [publishInfo, setPublishInfo] = useState<{
    has_subscription: boolean;
    has_credits: boolean;
    credits_balance: number;
    message: string | null;
  } | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/annonces/nouvelle');
      return;
    }
    
    // Vérifier si l'utilisateur est un vendeur
    if (user && user.role === 'buyer') {
      toast({
        title: 'Accès refusé',
        description: 'Seuls les vendeurs peuvent créer des annonces. Modifiez votre profil pour devenir vendeur.',
        variant: 'destructive',
      });
      router.push('/dashboard');
      return;
    }
    
    fetchCategories();
    checkCanPublish();
  }, [isAuthenticated, user, router]);

  const checkCanPublish = async () => {
    try {
      const response = await listingsAPI.canPublish();
      setCanPublish(response.data.can_publish);
      setPublishInfo({
        has_subscription: response.data.has_subscription,
        has_credits: response.data.has_credits,
        credits_balance: response.data.credits_balance,
        message: response.data.message,
      });
    } catch (error) {
      console.error('Error checking publish rights:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await categoriesAPI.getAll();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const newImages = files.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
    }));
    setImages((prev) => [...prev, ...newImages].slice(0, 10));
  };

  const removeImage = (index: number) => {
    setImages((prev) => {
      const newImages = [...prev];
      URL.revokeObjectURL(newImages[index].preview);
      newImages.splice(index, 1);
      return newImages;
    });
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Partial<FormData> = {};

    if (step === 1) {
      if (!formData.title.trim()) newErrors.title = 'Titre requis';
      if (formData.title.length < 5) newErrors.title = 'Minimum 5 caractères';
      if (!formData.category_id) newErrors.category_id = 'Catégorie requise';
    }

    if (step === 2) {
      if (!formData.description.trim()) newErrors.description = 'Description requise';
      if (formData.description.length < 20) newErrors.description = 'Minimum 20 caractères';
      if (!formData.condition) newErrors.condition = 'État requis';
    }

    if (step === 3) {
      if (!formData.price) newErrors.price = 'Prix requis';
      if (parseFloat(formData.price) <= 0) newErrors.price = 'Prix invalide';
      if (!formData.location.trim()) newErrors.location = 'Localisation requise';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, 4));
    }
  };

  const prevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);
    try {
      const data = new FormData();
      Object.entries(formData).forEach(([key, value]) => {
        data.append(key, value);
      });
      // Ajouter status pour publication directe
      data.append('status', 'published');
      // Envoyer les images avec le nom 'images' pour chaque fichier
      images.forEach((img) => {
        data.append('images', img.file);
      });

      await listingsAPI.create(data);
      toast({
        title: 'Annonce créée !',
        description: 'Votre annonce a été publiée avec succès',
        variant: 'success',
      });
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Erreur création annonce:', error.response?.data || error);
      const errorMessage = error.response?.data?.detail 
        || error.response?.data?.message 
        || JSON.stringify(error.response?.data) 
        || error.message 
        || 'Une erreur est survenue';
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const conditions = [
    { value: 'new', label: 'Neuf', description: 'Jamais utilisé, dans son emballage' },
    { value: 'like_new', label: 'Comme neuf', description: 'Utilisé une ou deux fois' },
    { value: 'good', label: 'Bon état', description: 'Quelques traces d\'utilisation' },
    { value: 'fair', label: 'État correct', description: 'Signes d\'usure visibles' },
    { value: 'poor', label: 'Usé', description: 'Fonctionnel mais très utilisé' },
  ];

  const steps = [
    { number: 1, title: 'Informations', icon: Tag },
    { number: 2, title: 'Description', icon: FileText },
    { number: 3, title: 'Prix & Lieu', icon: DollarSign },
    { number: 4, title: 'Photos', icon: ImageIcon },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4 max-w-3xl">
          {/* Bannière d'avertissement si pas de droits de publication */}
          {canPublish === false && publishInfo && (
            <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <AlertCircle className="w-6 h-6 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-amber-800 mb-2">
                    Publication non autorisée
                  </h3>
                  <p className="text-amber-700 mb-4">
                    {publishInfo.message || 'Vous devez avoir un abonnement actif ou des crédits pour publier une annonce.'}
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Button
                      onClick={() => router.push('/abonnements')}
                      className="bg-primary-600 hover:bg-primary-700"
                    >
                      Voir les abonnements
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => router.push('/credits')}
                      className="border-amber-600 text-amber-700 hover:bg-amber-100"
                    >
                      Acheter des crédits
                    </Button>
                  </div>
                  <div className="mt-4 text-sm text-amber-600">
                    <p>
                      • Abonnement actif : {publishInfo.has_subscription ? '✅ Oui' : '❌ Non'}
                    </p>
                    <p>
                      • Crédits disponibles : {publishInfo.credits_balance}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Loading state */}
          {canPublish === null && (
            <div className="mb-6 bg-gray-100 rounded-xl p-6 flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mr-3"></div>
              <span className="text-gray-600">Vérification de vos droits de publication...</span>
            </div>
          )}

          {/* Progress Steps */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.number} className="flex items-center">
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                      currentStep >= step.number
                        ? 'bg-primary-600 border-primary-600 text-white'
                        : 'border-gray-300 text-gray-400'
                    }`}
                  >
                    {currentStep > step.number ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`hidden sm:block w-full h-1 mx-2 rounded ${
                        currentStep > step.number ? 'bg-primary-600' : 'bg-gray-200'
                      }`}
                      style={{ width: '60px' }}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2">
              {steps.map((step) => (
                <span
                  key={step.number}
                  className={`text-xs font-medium ${
                    currentStep >= step.number ? 'text-primary-600' : 'text-gray-400'
                  }`}
                >
                  {step.title}
                </span>
              ))}
            </div>
          </div>

          {/* Form Card */}
          <div className="bg-white rounded-2xl shadow-sm p-8">
            {/* Step 1: Basic Info */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Informations générales
                  </h2>
                  <p className="text-gray-500">
                    Commencez par les informations de base de votre annonce
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Titre de l'annonce *
                    </label>
                    <Input
                      placeholder="Ex: iPhone 14 Pro Max 256Go"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      error={errors.title}
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      {formData.title.length}/100 caractères
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Catégorie *
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {categories.map((category) => (
                        <button
                          key={category.id}
                          type="button"
                          onClick={() => handleInputChange('category_id', category.id)}
                          className={`p-4 rounded-xl border-2 text-left transition-all ${
                            formData.category_id === category.id
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <span className="text-2xl mb-2 block">{category.icon}</span>
                          <span className="font-medium text-sm">{category.name}</span>
                        </button>
                      ))}
                    </div>
                    {errors.category_id && (
                      <p className="mt-1 text-sm text-red-500">{errors.category_id}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Type d'annonce
                    </label>
                    <div className="flex gap-4">
                      {['product', 'rental', 'service'].map((type) => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => handleInputChange('listing_type', type)}
                          className={`flex-1 p-3 rounded-lg border-2 text-center transition-all ${
                            formData.listing_type === type
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <span className="font-medium">
                            {type === 'product' && 'Vente'}
                            {type === 'rental' && 'Location'}
                            {type === 'service' && 'Service'}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Description */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Description détaillée
                  </h2>
                  <p className="text-gray-500">
                    Décrivez votre article en détail pour attirer les acheteurs
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description *
                    </label>
                    <Textarea
                      placeholder="Décrivez votre article : caractéristiques, état, raison de la vente..."
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                      rows={6}
                      error={errors.description}
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      {formData.description.length}/2000 caractères (minimum 20)
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      État de l'article *
                    </label>
                    <div className="space-y-2">
                      {conditions.map((condition) => (
                        <button
                          key={condition.value}
                          type="button"
                          onClick={() => handleInputChange('condition', condition.value)}
                          className={`w-full p-4 rounded-xl border-2 text-left transition-all flex items-center justify-between ${
                            formData.condition === condition.value
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div>
                            <span className="font-medium block">{condition.label}</span>
                            <span className="text-sm text-gray-500">{condition.description}</span>
                          </div>
                          {formData.condition === condition.value && (
                            <CheckCircle className="w-5 h-5 text-primary-600" />
                          )}
                        </button>
                      ))}
                    </div>
                    {errors.condition && (
                      <p className="mt-1 text-sm text-red-500">{errors.condition}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Price & Location */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Prix et localisation
                  </h2>
                  <p className="text-gray-500">
                    Définissez votre prix et votre zone géographique
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prix *
                    </label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <Input
                        type="number"
                        placeholder="0"
                        value={formData.price}
                        onChange={(e) => handleInputChange('price', e.target.value)}
                        className="pl-10"
                        error={errors.price}
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">
                        €
                      </span>
                    </div>
                    <div className="mt-2 flex items-start gap-2 text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">
                      <Info className="h-5 w-5 flex-shrink-0" />
                      <span>
                        Conseil : Consultez des annonces similaires pour fixer un prix attractif
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Localisation *
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <Input
                        placeholder="Ville ou code postal"
                        value={formData.location}
                        onChange={(e) => handleInputChange('location', e.target.value)}
                        className="pl-10"
                        error={errors.location}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Photos */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Photos
                  </h2>
                  <p className="text-gray-500">
                    Ajoutez jusqu'à 10 photos pour illustrer votre annonce
                  </p>
                </div>

                <div>
                  <div
                    className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-400 transition-colors cursor-pointer"
                    onClick={() => document.getElementById('image-upload')?.click()}
                  >
                    <input
                      id="image-upload"
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={handleImageUpload}
                    />
                    <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600 font-medium">
                      Cliquez pour ajouter des photos
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      JPG, PNG jusqu'à 10 Mo chacune
                    </p>
                  </div>

                  {images.length > 0 && (
                    <div className="mt-4 grid grid-cols-3 sm:grid-cols-5 gap-3">
                      {images.map((img, index) => (
                        <div key={index} className="relative aspect-square rounded-lg overflow-hidden">
                          <img
                            src={img.preview}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                          <button
                            type="button"
                            onClick={() => removeImage(index)}
                            className="absolute top-1 right-1 p-1 bg-black/50 rounded-full text-white hover:bg-black/70"
                          >
                            <X className="h-4 w-4" />
                          </button>
                          {index === 0 && (
                            <span className="absolute bottom-1 left-1 text-xs bg-primary-600 text-white px-2 py-0.5 rounded">
                              Principal
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <p className="mt-2 text-sm text-gray-500">
                    {images.length}/10 photos • La première sera l'image principale
                  </p>
                </div>

                {/* Summary */}
                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="font-semibold mb-3">Récapitulatif</h3>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Titre</dt>
                      <dd className="font-medium">{formData.title || '-'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Prix</dt>
                      <dd className="font-medium">{formData.price ? `${formData.price} €` : '-'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Localisation</dt>
                      <dd className="font-medium">{formData.location || '-'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Photos</dt>
                      <dd className="font-medium">{images.length}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between mt-8 pt-6 border-t">
              <Button
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 1}
              >
                Précédent
              </Button>

              {currentStep < 4 ? (
                <Button variant="gradient" onClick={nextStep} disabled={canPublish === false}>
                  Suivant
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              ) : (
                <Button
                  variant="gradient"
                  onClick={handleSubmit}
                  loading={isSubmitting}
                  disabled={canPublish === false || isSubmitting}
                >
                  {canPublish === false ? 'Publication non autorisée' : 'Publier l\'annonce'}
                </Button>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
