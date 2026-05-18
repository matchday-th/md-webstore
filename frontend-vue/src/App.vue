<template>
  <div class="min-h-screen bg-ink text-white">
    <div class="mx-auto max-w-7xl px-6 py-8 lg:px-10">
      <header class="panel mb-8 overflow-hidden">
        <div class="grid gap-4 px-6 py-6 lg:grid-cols-5 lg:px-8">
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Profiles</p>
            <p class="mt-3 text-3xl font-semibold">{{ profiles.length }}</p>
          </div>
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Products</p>
            <p class="mt-3 text-3xl font-semibold">{{ products.length }}</p>
          </div>
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Orders</p>
            <p class="mt-3 text-3xl font-semibold">{{ orders.length }}</p>
          </div>
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Inventory Value</p>
            <p class="mt-3 text-3xl font-semibold">{{ money(inventoryValue) }}</p>
          </div>
        </div>
      </header>

      <main v-if="ready && !errorMessage" class="space-y-8">
        <section class="panel overflow-hidden p-0">
          <div class="border-b border-white/10 bg-white px-6 text-ink">
            <div class="flex flex-wrap items-end gap-0 overflow-x-auto">
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'storefront' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'storefront'"
              >
                หน้าร้าน
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'warehouse' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'warehouse'"
              >
                คลัง
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'orders' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'orders'"
              >
                บิลออเดอร์
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'provider' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'provider'"
              >
                ร้านค้า
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'user' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'user'"
              >
                สมาชิก
              </button>
            </div>
          </div>

          <div class="p-6">
            <section v-if="workspaceTab === 'storefront'" class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
              <div class="panel-header">
                <div>
                  <p class="text-xs uppercase tracking-[0.22em] text-white/40">Banner Listing</p>
                  <h2 class="mt-2 text-2xl font-semibold">Featured products drive the storefront.</h2>
                </div>
                <MegaphoneIcon class="h-6 w-6 text-white/55" />
              </div>

              <div class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
                <div
                  v-for="product in featuredProducts"
                  :key="product.id"
                  class="rounded-[1.8rem] border border-white/10 bg-black/20 p-5"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-lg font-medium">{{ product.name }}</p>
                      <p class="mt-1 text-sm text-white/50">{{ product.description }}</p>
                    </div>
                    <span class="chip">{{ product.category }}</span>
                  </div>

                  <div class="mt-5">
                    <p class="text-xs uppercase tracking-[0.2em] text-white/35">Price</p>
                    <p class="mt-1 text-xl font-semibold">{{ money(product.price) }}</p>
                  </div>
                </div>
              </div>
            </section>

            <section v-else-if="workspaceTab === 'warehouse'" class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
              <div class="panel-header">
                <div>
                  <p class="text-xs uppercase tracking-[0.22em] text-white/40">Warehouse</p>
                  <h2 class="mt-2 text-2xl font-semibold">Inventory updates directly from product and order activity.</h2>
                </div>
                <ArchiveBoxIcon class="h-6 w-6 text-white/55" />
              </div>

              <div class="space-y-3">
                <div
                  v-for="product in products"
                  :key="product.id"
                  class="flex items-center justify-between rounded-[1.4rem] border border-white/10 bg-white/[0.025] px-4 py-4"
                >
                  <div>
                    <p class="font-medium">{{ product.name }}</p>
                    <p class="mt-1 text-sm text-white/45">{{ product.sku }} · {{ product.category }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-lg font-semibold">{{ product.stock }} units</p>
                    <p
                      class="mt-1 text-xs uppercase tracking-[0.16em]"
                      :class="Number(product.stock) <= 5 ? 'text-amber-300' : 'text-white/35'"
                    >
                      {{ Number(product.stock) <= 5 ? "Low stock" : "Healthy stock" }}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section v-else-if="workspaceTab === 'orders'" class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
              <div class="panel-header">
                <div>
                  <p class="text-xs uppercase tracking-[0.22em] text-white/40">Order</p>
                  <h2 class="mt-2 text-2xl font-semibold">Order queue linked to warehouse movement.</h2>
                </div>
                <ClipboardDocumentListIcon class="h-6 w-6 text-white/55" />
              </div>

              <div class="space-y-3">
                <div
                  v-for="order in orders"
                  :key="order.id"
                  class="rounded-[1.5rem] border border-white/10 bg-white/[0.025] p-4"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm uppercase tracking-[0.18em] text-white/35">Order #{{ order.id }}</p>
                      <p class="mt-2 text-lg font-medium">{{ order.user_name }}</p>
                    </div>
                    <span class="chip">{{ order.status }}</span>
                  </div>
                  <div class="mt-4 space-y-3">
                    <div
                      v-for="item in order.items"
                      :key="`${order.id}-${item.productId}`"
                      class="rounded-[1.2rem] border border-white/10 bg-black/20 px-4 py-3"
                    >
                      <div class="flex items-start justify-between gap-4">
                        <div>
                          <p class="font-medium">{{ item.name }}</p>
                          <p class="mt-1 text-sm text-white/45">ร้านค้า: {{ item.providerName || "Unknown shop" }}</p>
                        </div>
                        <div class="text-right">
                          <p class="text-sm text-white/60">x{{ item.quantity }}</p>
                          <p class="mt-1 font-medium">{{ money(item.price * item.quantity) }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="mt-4 flex items-center justify-between">
                    <p class="text-sm text-white/45">{{ order.notes || "No notes" }}</p>
                    <p class="text-lg font-semibold">{{ money(order.total) }}</p>
                  </div>
                </div>
              </div>
            </section>

            <section v-else-if="workspaceTab === 'provider'" class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">Provider</p>
                    <h2 class="mt-2 text-2xl font-semibold">➕ Add New Shop</h2>
                  </div>
                  <ArchiveBoxIcon class="h-6 w-6 text-white/55" />
                </div>

                <form class="space-y-4" @submit.prevent="submitShop">
                  <div>
                    <label class="label">Owner Provider</label>
                    <select v-model="shopForm.provider_id" class="field" required>
                      <option value="" disabled>Select provider</option>
                      <option v-for="provider in providers" :key="provider.provider_id" :value="provider.provider_id">
                        {{ provider.provider_name }} · {{ provider.shop_count || 0 }} shops
                      </option>
                    </select>
                    <p class="mt-2 text-sm text-white/45">Use this dropdown to choose the main provider account that will own the new shop.</p>
                    <div v-if="selectedProviderInfo && selectedProviderInfo.shop_names?.length" class="mt-3 flex flex-wrap gap-2">
                      <span
                        v-for="shopName in selectedProviderInfo.shop_names"
                        :key="shopName"
                        class="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60"
                      >
                        {{ shopName }}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label class="label">Shop Name *</label>
                    <input v-model="shopForm.name" class="field" type="text" placeholder="e.g., Kanoon Footwear" required />
                  </div>
                  <div>
                    <label class="label">Shop Email</label>
                    <input v-model="shopForm.email" class="field" type="email" placeholder="optional-shop@email.com" />
                  </div>
                  <div class="flex flex-wrap gap-3">
                    <button class="button-primary" type="submit">Create Shop</button>
                    <button class="button-secondary" type="button" @click="resetShopForm">Reset</button>
                  </div>
                </form>
              </article>

              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">Shop Directory</p>
                    <h2 class="mt-2 text-2xl font-semibold">Current shops from the user storefront.</h2>
                  </div>
                  <ClipboardDocumentListIcon class="h-6 w-6 text-white/55" />
                </div>

                <div v-if="shopMessage" class="mb-4 rounded-[1.2rem] border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
                  {{ shopMessage }}
                </div>

                <div v-if="selectedProviderShops.length" class="space-y-3">
                  <div
                    v-for="shop in selectedProviderShops"
                    :key="shop.provider_id"
                    class="rounded-[1.5rem] border border-white/10 bg-white/[0.025] px-4 py-4"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div>
                        <p class="font-medium">{{ shop.provider_name }}</p>
                        <p class="mt-1 text-sm text-white/45">{{ shop.provider_id }}</p>
                        <p class="mt-2 text-xs uppercase tracking-[0.16em] text-white/35">{{ shop.product_count || 0 }} products in this shop</p>
                      </div>
                      <div class="flex items-center gap-2">
                        <span class="chip">store</span>
                        <button
                          v-if="shop.owner_provider_id"
                          class="rounded-full border border-red-400/20 bg-red-400/10 px-3 py-1 text-xs text-red-200 transition hover:bg-red-400/20"
                          type="button"
                          @click="removeShop(shop)"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="rounded-[1.5rem] border border-dashed border-white/10 px-4 py-8 text-center text-sm text-white/40">
                  No shops loaded for this provider yet.
                </div>
              </article>
            </section>

            <section v-else class="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">User</p>
                    <h2 class="mt-2 text-2xl font-semibold">Member profile manager.</h2>
                  </div>
                  <UserCircleIcon class="h-6 w-6 text-white/55" />
                </div>

                <form class="space-y-3" @submit.prevent="submitProfile">
                  <div>
                    <label class="label">Full Name</label>
                    <input v-model="profileForm.name" class="field" type="text" required />
                  </div>
                  <div class="grid gap-3 md:grid-cols-2">
                    <div>
                      <label class="label">Email</label>
                      <input v-model="profileForm.email" class="field" type="email" required />
                    </div>
                    <div>
                      <label class="label">Role</label>
                      <input v-model="profileForm.role" class="field" type="text" required />
                    </div>
                  </div>
                  <div>
                    <label class="label">Phone</label>
                    <input v-model="profileForm.phone" class="field" type="text" />
                  </div>
                  <div>
                    <label class="label">Address</label>
                    <textarea v-model="profileForm.address" class="field min-h-[110px]"></textarea>
                  </div>
                  <div class="flex flex-wrap gap-3">
                    <button class="button-primary" type="submit">{{ profileForm.id ? "Update Profile" : "Create Profile" }}</button>
                    <button class="button-secondary" type="button" @click="resetProfileForm">Reset</button>
                    <button v-if="profileForm.id" class="button-danger" type="button" @click="removeProfile(profileForm.id)">Delete</button>
                  </div>
                </form>
              </article>

              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-4">
                <div class="space-y-3">
                  <button
                    v-for="profile in profiles"
                    :key="profile.id"
                    class="flex w-full items-center justify-between rounded-[1.4rem] border border-white/10 bg-white/[0.025] px-4 py-4 text-left transition hover:border-white/25"
                    @click="editProfile(profile)"
                  >
                    <div>
                      <p class="font-medium">{{ profile.name }}</p>
                      <p class="mt-1 text-sm text-white/45">{{ profile.role }} · {{ profile.email }}</p>
                    </div>
                    <ChevronRightIcon class="h-5 w-5 text-white/35" />
                  </button>
                </div>
              </article>
            </section>
          </div>
        </section>
      </main>

      <div v-else-if="errorMessage" class="panel p-12 text-center text-white/75">
        {{ errorMessage }}
      </div>
      <div v-else class="panel p-12 text-center text-white/60">Connecting to live database...</div>
    </div>
  </div>
</template>

<script>
import {
  ArchiveBoxIcon,
  ChevronRightIcon,
  ClipboardDocumentListIcon,
  CreditCardIcon,
  MegaphoneIcon,
  ShoppingBagIcon,
  UserCircleIcon
} from "@heroicons/vue/24/outline";
import { useAppStore } from "./stores/app";
import { studioApi } from "./services/api";

function profileDefaults() {
  return {
    id: null,
    name: "",
    email: "",
    role: "Buyer",
    phone: "",
    address: ""
  };
}

function shopDefaults(providerId = "") {
  return {
    provider_id: providerId,
    name: "",
    email: ""
  };
}

export default {
  name: "App",
  components: {
    ArchiveBoxIcon,
    ChevronRightIcon,
    ClipboardDocumentListIcon,
    MegaphoneIcon,
    UserCircleIcon
  },
  data() {
    return {
      store: null,
      selectedProfileId: null,
      workspaceTab: "storefront",
      profileForm: profileDefaults(),
      providers: [],
      shopForm: shopDefaults(),
      shopMessage: ""
    };
  },
  computed: {
    ready() {
      return this.store?.ready || false;
    },
    profiles() {
      return this.store?.profiles || [];
    },
    products() {
      return this.store?.products || [];
    },
    selectedProviderInfo() {
      return this.providers.find((provider) => provider.provider_id === this.shopForm.provider_id) || null;
    },
    selectedProviderShops() {
      return this.selectedProviderInfo?.shops || [];
    },
    orders() {
      return this.store?.orders || [];
    },
    featuredProducts() {
      return this.store?.featuredProducts || [];
    },
    inventoryValue() {
      return this.store?.inventoryValue || 0;
    },
    activeProfile() {
      return this.store?.activeProfile || null;
    },
    errorMessage() {
      return this.store?.error || "";
    }
  },
  async mounted() {
    this.store = useAppStore();
    await this.store.initialize();
    this.selectedProfileId = this.store.activeProfileId;
    this.hydrateForms();
    await this.loadProviders();
  },
  methods: {
    money(value) {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
      }).format(Number(value || 0));
    },
    hydrateForms() {
      if (this.activeProfile) {
        this.profileForm = { ...this.activeProfile };
      } else {
        this.profileForm = profileDefaults();
      }
      this.selectedProfileId = this.store.activeProfileId;
    },
    async loadProviders() {
      try {
        const data = await studioApi.listProviders();
        this.providers = data.providers || [];
        const fallbackProviderId = this.providers[0]?.provider_id || "";
        if (!this.shopForm.provider_id) {
          this.shopForm.provider_id = fallbackProviderId;
        }
      } catch (error) {
        this.shopMessage = error.message || "Unable to load providers.";
      }
    },
    onProfileChange() {
      this.store.selectProfile(this.selectedProfileId);
      this.profileForm = this.activeProfile ? { ...this.activeProfile } : profileDefaults();
    },
    async submitProfile() {
      await this.store.saveProfile({ ...this.profileForm });
      this.resetProfileForm();
      this.selectedProfileId = this.store.activeProfileId;
    },
    resetProfileForm() {
      this.profileForm = this.activeProfile ? { ...this.activeProfile } : profileDefaults();
    },
    editProfile(profile) {
      this.profileForm = { ...profile };
      this.workspaceTab = "user";
    },
    async removeProfile(id) {
      await this.store.deleteProfile(id);
      this.resetProfileForm();
      this.selectedProfileId = this.store.activeProfileId;
    },
    resetShopForm() {
      this.shopForm = shopDefaults(this.providers[0]?.provider_id || "");
      this.shopMessage = "";
    },
    async submitShop() {
      await studioApi.createProviderShop(this.shopForm.provider_id, {
        name: this.shopForm.name,
        email: this.shopForm.email
      });
      const createdName = this.shopForm.name;
      this.resetShopForm();
      this.shopMessage = `Created shop: ${createdName}`;
      await this.loadProviders();
      await this.store.reloadAll();
    },
    async removeShop(shop) {
      if (!window.confirm(`Delete shop "${shop.provider_name}"?`)) {
        return;
      }
      await studioApi.deleteProviderShop(shop.provider_id);
      this.shopMessage = `Deleted shop: ${shop.provider_name}`;
      await this.loadProviders();
      await this.store.reloadAll();
    }
  },
  watch: {
    activeProfile(nextProfile) {
      if (!this.profileForm.id && nextProfile) {
        this.profileForm = { ...nextProfile };
      }
    }
  }
};
</script>
