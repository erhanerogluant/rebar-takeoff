class MeshData:
    # Q Tipi Hasırlar
    Q_TYPE_MESHES = {
        'Q106': {'weight': 1.66, 'diameter': 4.5, 'spacing': 150},
        'Q131': {'weight': 2.06, 'diameter': 5.0, 'spacing': 150},
        'Q158': {'weight': 2.49, 'diameter': 5.5, 'spacing': 150},
        'Q188': {'weight': 2.96, 'diameter': 6.0, 'spacing': 150},
        'Q221': {'weight': 3.47, 'diameter': 6.5, 'spacing': 150},
        'Q257': {'weight': 4.03, 'diameter': 7.0, 'spacing': 150},
        'Q257/188': {'weight': 3.49, 'diameter': 7.0, 'spacing': 150},
        'Q295': {'weight': 4.62, 'diameter': 7.5, 'spacing': 150},
        'Q295/257': {'weight': 4.33, 'diameter': 7.5, 'spacing': 150},
        'Q295/221': {'weight': 4.04, 'diameter': 7.5, 'spacing': 150},
        'Q295/188': {'weight': 3.79, 'diameter': 7.5, 'spacing': 150},
        'Q295/158': {'weight': 3.56, 'diameter': 7.5, 'spacing': 150},
        'Q317': {'weight': 5.00, 'diameter': 7.8, 'spacing': 150},
        'Q317/295': {'weight': 4.81, 'diameter': 7.8, 'spacing': 150},
        'Q317/257': {'weight': 4.52, 'diameter': 7.8, 'spacing': 150},
        'Q317/221': {'weight': 4.24, 'diameter': 7.8, 'spacing': 150},
        'Q317/188': {'weight': 3.98, 'diameter': 7.8, 'spacing': 150},
        'Q335': {'weight': 5.26, 'diameter': 8.0, 'spacing': 150},
        'Q335/317': {'weight': 5.13, 'diameter': 8.0, 'spacing': 150},
        'Q335/295': {'weight': 4.94, 'diameter': 8.0, 'spacing': 150},
        'Q335/257': {'weight': 4.64, 'diameter': 8.0, 'spacing': 150},
        'Q335/221': {'weight': 4.37, 'diameter': 8.0, 'spacing': 150},
        'Q335/188': {'weight': 4.11, 'diameter': 8.0, 'spacing': 150},
        'Q377': {'weight': 5.94, 'diameter': 8.5, 'spacing': 150},
        'Q377/335': {'weight': 5.60, 'diameter': 8.5, 'spacing': 150},
        'Q377/317': {'weight': 5.47, 'diameter': 8.5, 'spacing': 150},
        'Q377/295': {'weight': 5.28, 'diameter': 8.5, 'spacing': 150},
        'Q377/257': {'weight': 4.98, 'diameter': 8.5, 'spacing': 150},
        'Q377/221': {'weight': 4.71, 'diameter': 8.5, 'spacing': 150},
        'Q377/188': {'weight': 4.45, 'diameter': 8.5, 'spacing': 150},
        'Q424': {'weight': 6.66, 'diameter': 9.0, 'spacing': 150},
        'Q424/377': {'weight': 6.30, 'diameter': 9.0, 'spacing': 150},
        'Q424/335': {'weight': 5.96, 'diameter': 9.0, 'spacing': 150},
        'Q424/317': {'weight': 5.98, 'diameter': 9.0, 'spacing': 150},
        'Q424/295': {'weight': 5.64, 'diameter': 9.0, 'spacing': 150},
        'Q424/257': {'weight': 5.34, 'diameter': 9.0, 'spacing': 150},
        'Q424/221': {'weight': 5.07, 'diameter': 9.0, 'spacing': 150},
        'Q443': {'weight': 6.96, 'diameter': 9.2, 'spacing': 150},
        'Q443/377': {'weight': 6.45, 'diameter': 9.2, 'spacing': 150},
        'Q443/335': {'weight': 6.11, 'diameter': 9.2, 'spacing': 150},
        'Q443/317': {'weight': 5.98, 'diameter': 9.2, 'spacing': 150},
        'Q443/295': {'weight': 5.79, 'diameter': 9.2, 'spacing': 150},
        'Q443/257': {'weight': 5.49, 'diameter': 9.2, 'spacing': 150},
        'Q443/221': {'weight': 5.22, 'diameter': 9.2, 'spacing': 150},
        'Q473': {'weight': 7.42, 'diameter': 9.5, 'spacing': 150},
        'Q503': {'weight': 7.89, 'diameter': 8.0, 'spacing': 100},
        'Q513': {'weight': 8.09, 'diameter': 8.1, 'spacing': 100},
        'Q513/257': {'weight': 6.06, 'diameter': 8.1, 'spacing': 100},
        'Q524': {'weight': 8.22, 'diameter': 10.0, 'spacing': 150},
        'Q524/443': {'weight': 7.59, 'diameter': 10.0, 'spacing': 150},
        'Q524/424': {'weight': 7.44, 'diameter': 10.0, 'spacing': 150},
        'Q524/377': {'weight': 7.08, 'diameter': 10.0, 'spacing': 150},
        'Q524/335': {'weight': 6.74, 'diameter': 10.0, 'spacing': 150},
        'Q524/317': {'weight': 6.61, 'diameter': 10.0, 'spacing': 150},
        'Q524/295': {'weight': 6.42, 'diameter': 10.0, 'spacing': 150},
        'Q524/257': {'weight': 6.12, 'diameter': 10.0, 'spacing': 150},
        'Q589': {'weight': 9.24, 'diameter': 10.6, 'spacing': 150},
        'Q589/589': {'weight': 9.33, 'diameter': 8.7, 'spacing': 100},
        'Q589/503': {'weight': 8.61, 'diameter': 8.7, 'spacing': 100},
        'Q589/378': {'weight': 7.64, 'diameter': 8.7, 'spacing': 100},
        'Q589/335': {'weight': 7.30, 'diameter': 8.7, 'spacing': 100},
        'Q589/317': {'weight': 7.17, 'diameter': 8.7, 'spacing': 100},
        'Q589/295': {'weight': 6.98, 'diameter': 8.7, 'spacing': 100},
        'Q634': {'weight': 9.95, 'diameter': 11.0, 'spacing': 150},
        'Q636': {'weight': 9.99, 'diameter': 9.0, 'spacing': 100},
        'Q636/424': {'weight': 8.32, 'diameter': 9.0, 'spacing': 100},
        'Q709/424': {'weight': 8.89, 'diameter': 9.5, 'spacing': 100},
        'Q754': {'weight': 11.84, 'diameter': 12.0, 'spacing': 150},
        'Q785': {'weight': 12.33, 'diameter': 10.0, 'spacing': 100},
        'Q785/295': {'weight': 8.48, 'diameter': 10.0, 'spacing': 100},
        'Q785/257': {'weight': 8.18, 'diameter': 10.0, 'spacing': 100},
        'Q950': {'weight': 14.92, 'diameter': 11.0, 'spacing': 100},
        'Q1131': {'weight': 17.76, 'diameter': 12.0, 'spacing': 100},
    }

    # R Tipi Hasırlar
    R_TYPE_MESHES = {
        'R106': {'weight': 1.33, 'diameter': 4.5, 'spacing': 150},
        'R131': {'weight': 1.65, 'diameter': 5.0, 'spacing': 150},
        'R158': {'weight': 1.86, 'diameter': 5.5, 'spacing': 150},
        'R188': {'weight': 2.10, 'diameter': 6.0, 'spacing': 150},
        'R221': {'weight': 2.36, 'diameter': 6.5, 'spacing': 150},
        'R257': {'weight': 2.63, 'diameter': 7.0, 'spacing': 150},
        'R295': {'weight': 2.93, 'diameter': 7.5, 'spacing': 150},
        'R317': {'weight': 3.11, 'diameter': 7.8, 'spacing': 150},
        'R335': {'weight': 3.25, 'diameter': 8.0, 'spacing': 150},
        'R377': {'weight': 3.58, 'diameter': 8.5, 'spacing': 150},
        'R443': {'weight': 4.22, 'diameter': 9.2, 'spacing': 150},
        'R513': {'weight': 4.92, 'diameter': 10.0, 'spacing': 150},
        'R589': {'weight': 5.66, 'diameter': 10.6, 'spacing': 150},
    }

    # TR Tipi Hasırlar
    TR_TYPE_MESHES = {
        'TR131': {'weight': 1.59, 'diameter': 5.0, 'spacing': 300},
        'TR158': {'weight': 1.81, 'diameter': 5.0, 'spacing': 300},
        'TR188': {'weight': 2.04, 'diameter': 5.0, 'spacing': 300},
        'TR221': {'weight': 2.29, 'diameter': 5.0, 'spacing': 300},
        'TR257': {'weight': 2.57, 'diameter': 5.0, 'spacing': 300},
        'TR295': {'weight': 2.86, 'diameter': 5.0, 'spacing': 300},
        'TR317': {'weight': 3.04, 'diameter': 5.0, 'spacing': 300},
        'TR335': {'weight': 3.18, 'diameter': 5.0, 'spacing': 300},
        'TR377': {'weight': 3.51, 'diameter': 5.0, 'spacing': 300},
        'TR443': {'weight': 4.13, 'diameter': 5.5, 'spacing': 300},
        'TR513': {'weight': 4.81, 'diameter': 6.0, 'spacing': 300},
        'TR524': {'weight': 4.90, 'diameter': 6.0, 'spacing': 300},
        'TR589': {'weight': 5.54, 'diameter': 6.5, 'spacing': 300},
    }

    @classmethod
    def get_mesh_data(cls, mesh_code):
        """Hasır koduna göre veri döndür"""
        # Kodu temizle (Q257/257 -> Q257)
        clean_code = mesh_code.split('/')[0] if '/' in mesh_code else mesh_code
        
        # Uygun tablodan veriyi al
        if clean_code.startswith('Q'):
            return cls.Q_TYPE_MESHES.get(clean_code)
        elif clean_code.startswith('TR'):
            return cls.TR_TYPE_MESHES.get(clean_code)
        elif clean_code.startswith('R'):
            return cls.R_TYPE_MESHES.get(clean_code)
        return None

    @classmethod
    def get_weight_per_m2(cls, mesh_code):
        """Hasır koduna göre birim ağırlık döndür (kg/m²)"""
        mesh_data = cls.get_mesh_data(mesh_code)
        return mesh_data['weight'] if mesh_data else 0

    @classmethod
    def get_properties(cls, mesh_code):
        """Hasır koduna göre çap ve aralık döndür"""
        mesh_data = cls.get_mesh_data(mesh_code)
        if mesh_data:
            return mesh_data['diameter'], mesh_data['spacing']
        return 0, 0 